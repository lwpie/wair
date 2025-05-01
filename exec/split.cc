#include <cassert>
#include <filesystem>
#include <fstream>
#include <iostream>
#include <memory>
#include <vector>

#include <arrow/api.h>
#include <arrow/io/api.h>
#include <arrow/io/file.h>
#include <arrow/util/logging.h>
#include <parquet/api/reader.h>
#include <parquet/api/writer.h>
#include <parquet/arrow/reader.h>
#include <parquet/arrow/writer.h>
#include <parquet/exception.h>

#include <boost/core/null_deleter.hpp>

constexpr int64_t PER_N = 1000;
constexpr int64_t ROW_GROUP_SIZE = 32000000;

int main(int argc, char **argv) {
  std::cerr << std::unitbuf;

  std::filesystem::path basename =
      std::filesystem::path(argv[1]).replace_extension("");
  if (std::filesystem::exists(basename))
    std::filesystem::remove_all(basename);
  std::filesystem::create_directory(basename);

  std::unique_ptr<parquet::ParquetFileReader> pq_reader =
      parquet::ParquetFileReader::OpenFile(argv[1]);

  std::shared_ptr<parquet::FileMetaData> metadata = pq_reader->metadata();
  //   std::cerr << metadata->schema()->ToString() << std::endl;

  std::shared_ptr<parquet::schema::GroupNode> schema =
      std::shared_ptr<parquet::schema::GroupNode>(
          const_cast<parquet::schema::GroupNode *>(
              metadata->schema()->group_node()),
          boost::null_deleter());

  //   std::cerr << metadata->num_rows() << std::endl;
  //   std::cerr << metadata->num_row_groups() << std::endl;
  //   std::cerr << metadata->num_columns() << std::endl << std::endl;

  // init memory pool
  struct BYTE_ARRAY_BUFFER {
    parquet::ByteArray *ptr;
    uint8_t *buffer;
    int64_t len;
    int64_t head;
  };

  void **pool = new void *[metadata->num_columns()];
#pragma omp parallel for num_threads(metadata->num_columns())
  for (int c = 0; c < metadata->num_columns(); ++c) {
    switch (pq_reader->RowGroup(0)->Column(c)->type()) {
    case parquet::Type::BOOLEAN:
      pool[c] = (void *)new bool[metadata->num_rows()];
      break;
    case parquet::Type::INT32:
      pool[c] = (void *)new int32_t[metadata->num_rows()];
      break;
    case parquet::Type::INT64:
      pool[c] = (void *)new int64_t[metadata->num_rows()];
      break;
    case parquet::Type::FLOAT:
      pool[c] = (void *)new float[metadata->num_rows()];
      break;
    case parquet::Type::DOUBLE:
      pool[c] = (void *)new double[metadata->num_rows()];
      break;
    case parquet::Type::BYTE_ARRAY: {
      BYTE_ARRAY_BUFFER *byte_array_buffer = new BYTE_ARRAY_BUFFER;
      pool[c] = (void *)byte_array_buffer;
      byte_array_buffer->ptr = new parquet::ByteArray[metadata->num_rows()];
      int64_t len = 0;
      for (int r = 0; r < metadata->num_row_groups(); ++r)
        len += metadata->RowGroup(r)->ColumnChunk(c)->total_uncompressed_size();
      byte_array_buffer->buffer = new uint8_t[len];
      byte_array_buffer->len = len;
      byte_array_buffer->head = 0;
      break;
    }
    case parquet::Type::FIXED_LEN_BYTE_ARRAY:
      assert(false);
      break;
    }
  }
  std::cerr << 'p';

// read data into memory
#pragma omp parallel for num_threads(metadata->num_columns())
  for (int c = 0; c < metadata->num_columns(); ++c) {
    int64_t head = 0;
    for (int r = 0; r < metadata->num_row_groups(); ++r) {
      std::shared_ptr<parquet::ColumnReader> col_reader =
          pq_reader->RowGroup(r)->Column(c);
      int64_t batch_size = metadata->RowGroup(r)->num_rows();
      int64_t count;
      switch (col_reader->type()) {
      case parquet::Type::BOOLEAN: {
        parquet::BoolReader *bool_reader =
            static_cast<parquet::BoolReader *>(col_reader.get());
        bool_reader->ReadBatch(batch_size, nullptr, nullptr,
                               (bool *)pool[c] + head, &count);
        assert(count == batch_size);
        head += batch_size;
        break;
      }
      case parquet::Type::INT32: {
        parquet::Int32Reader *int32_reader =
            static_cast<parquet::Int32Reader *>(col_reader.get());
        int32_reader->ReadBatch(batch_size, nullptr, nullptr,
                                (int32_t *)pool[c] + head, &count);
        assert(count == batch_size);
        head += batch_size;
        break;
      }
      case parquet::Type::INT64: {
        parquet::Int64Reader *int64_reader =
            static_cast<parquet::Int64Reader *>(col_reader.get());
        int64_reader->ReadBatch(batch_size, nullptr, nullptr,
                                (int64_t *)pool[c] + head, &count);
        assert(count == batch_size);
        head += batch_size;
        break;
      }
      case parquet::Type::FLOAT: {
        parquet::FloatReader *float_reader =
            static_cast<parquet::FloatReader *>(col_reader.get());
        float_reader->ReadBatch(batch_size, nullptr, nullptr,
                                (float *)pool[c] + head, &count);
        assert(count == batch_size);
        head += batch_size;
        break;
      }
      case parquet::Type::DOUBLE: {
        parquet::DoubleReader *double_reader =
            static_cast<parquet::DoubleReader *>(col_reader.get());
        double_reader->ReadBatch(batch_size, nullptr, nullptr,
                                 (double *)pool[c] + head, &count);
        assert(count == batch_size);
        head += batch_size;
        break;
      }
      case parquet::Type::BYTE_ARRAY: {
        parquet::ByteArrayReader *byte_array_reader =
            static_cast<parquet::ByteArrayReader *>(col_reader.get());
        BYTE_ARRAY_BUFFER *byte_array_buffer = (BYTE_ARRAY_BUFFER *)pool[c];
        parquet::ByteArray *byte_array = byte_array_buffer->ptr;
        for (int i = 0; i < batch_size; ++i) {
          int16_t def_level =
              metadata->schema()->Column(c)->max_definition_level();
          byte_array_reader->ReadBatch(1, &def_level, nullptr,
                                       byte_array + head + i, &count);
          // if (!byte_array[head + i].len)
          //   continue;
          assert(count == 1);
          if (byte_array_buffer->head + byte_array[head + i].len >
              byte_array_buffer->len) {
            byte_array_buffer->buffer =
                new uint8_t[byte_array_buffer->len] - byte_array_buffer->len;
            byte_array_buffer->head = byte_array_buffer->len;
            byte_array_buffer->len *= 2;
          }
          memcpy(byte_array_buffer->buffer + byte_array_buffer->head,
                 byte_array[head + i].ptr, byte_array[head + i].len);
          byte_array[head + i].ptr =
              byte_array_buffer->buffer + byte_array_buffer->head;
          byte_array_buffer->head += byte_array[head + i].len;
        }
        head += batch_size;
        break;
      }
      case parquet::Type::FIXED_LEN_BYTE_ARRAY: {
        assert(false);
        break;
      }
      }
    }
  }
  std::cerr << '\r' << 'r';

  // pq_reader->Close();

  // traverse and write to file
  std::filesystem::current_path(basename);
  int64_t file_id = 0;
  std::cerr << file_id << ' ';

  std::shared_ptr<arrow::io::FileOutputStream> outfile;
  PARQUET_ASSIGN_OR_THROW(outfile, arrow::io::FileOutputStream::Open(
                                       std::to_string(file_id) + ".parquet"));

  parquet::WriterProperties::Builder builder;
  builder.compression(metadata->RowGroup(0)->ColumnChunk(0)->compression());
  std::shared_ptr<parquet::WriterProperties> wr_props = builder.build();

  std::shared_ptr<parquet::ParquetFileWriter> pq_writer =
      parquet::ParquetFileWriter::Open(outfile, schema, wr_props);
  parquet::RowGroupWriter *rg_writer = pq_writer->AppendBufferedRowGroup();

  int64_t head = 0;

  while (head < metadata->num_rows()) {
    int64_t N = std::min(PER_N, metadata->num_rows() - head);
    int64_t estimated_bytes = 0;

#pragma omp parallel for num_threads(metadata->num_columns())
    for (int c = 0; c < metadata->num_columns(); ++c) {
      switch (pq_reader->RowGroup(0)->Column(c)->type()) {
      case parquet::Type::BOOLEAN: {
        parquet::BoolWriter *bool_writer =
            static_cast<parquet::BoolWriter *>(rg_writer->column(c));
        int16_t def_level =
            metadata->schema()->Column(c)->max_definition_level();
        bool *bool_array = (bool *)pool[c];
        assert(bool_writer->WriteBatch(N, &def_level, nullptr,
                                       bool_array + head) == N);
        break;
      }
      case parquet::Type::INT32: {
        parquet::Int32Writer *int32_writer =
            static_cast<parquet::Int32Writer *>(rg_writer->column(c));
        int16_t def_level =
            metadata->schema()->Column(c)->max_definition_level();
        int32_t *int32_array = (int32_t *)pool[c];
        for (int i = 0; i < N; ++i)
          assert(int32_writer->WriteBatch(1, &def_level, nullptr,
                                          int32_array + head + i) == 1);
        // int32_writer->WriteBatch(N, &def_level, nullptr, int32_array + head);
        break;
      }
      case parquet::Type::INT64: {
        parquet::Int64Writer *int64_writer =
            static_cast<parquet::Int64Writer *>(rg_writer->column(c));
        int16_t def_level =
            metadata->schema()->Column(c)->max_definition_level();
        int64_t *int64_array = (int64_t *)pool[c];
        for (int i = 0; i < N; ++i)
          assert(int64_writer->WriteBatch(1, &def_level, nullptr,
                                          int64_array + head + i) == 1);
        // int64_writer->WriteBatch(N, &def_level, nullptr, int64_array + head);
        break;
      }
      case parquet::Type::FLOAT: {
        parquet::FloatWriter *float_writer =
            static_cast<parquet::FloatWriter *>(rg_writer->column(c));
        int16_t def_level =
            metadata->schema()->Column(c)->max_definition_level();
        float *float_array = (float *)pool[c];
        assert(float_writer->WriteBatch(N, &def_level, nullptr,
                                        float_array + head) == N);
        break;
      }
      case parquet::Type::DOUBLE: {
        parquet::DoubleWriter *double_writer =
            static_cast<parquet::DoubleWriter *>(rg_writer->column(c));
        int16_t def_level =
            metadata->schema()->Column(c)->max_definition_level();
        double *double_array = (double *)pool[c];
        // for (int i = 0; i < N; ++i)
        //   assert(double_writer->WriteBatch(1, &def_level, nullptr,
        //                                    double_array + head + i) == 1);
        assert(double_writer->WriteBatch(N, &def_level, nullptr,
                                         double_array + head) == N);
        break;
      }
      case parquet::Type::BYTE_ARRAY: {
        parquet::ByteArrayWriter *byte_array_writer =
            static_cast<parquet::ByteArrayWriter *>(rg_writer->column(c));
        int16_t def_level =
            metadata->schema()->Column(c)->max_definition_level();
        BYTE_ARRAY_BUFFER *byte_array_buffer = (BYTE_ARRAY_BUFFER *)pool[c];
        parquet::ByteArray *byte_array = byte_array_buffer->ptr;
        for (int i = 0; i < N; ++i)
          assert(byte_array_writer->WriteBatch(1, &def_level, nullptr,
                                               byte_array + head + i) == 1);

        // assert(byte_array_writer->WriteBatch(N, &def_level, nullptr,
        //                                      byte_array + head) == N);
        break;
      }
      case parquet::Type::FIXED_LEN_BYTE_ARRAY:
        assert(false);
        break;
      }

      estimated_bytes += rg_writer->column(c)->estimated_buffered_value_bytes();
    }

    head += N;

    // std::cerr << rg_writer->total_bytes_written() << std::endl;
    // std::cerr << rg_writer->total_compressed_bytes_written() << std::endl;
    // std::cerr << rg_writer->total_compressed_bytes() << std::endl;
    // std::cerr << estimated_bytes << std::endl;
    // if (rg_writer->total_bytes_written())
    //   std::cerr << "Total: "
    //             << rg_writer->total_compressed_bytes_written() +
    //                    rg_writer->total_compressed_bytes() +
    //                    estimated_bytes *
    //                        rg_writer->total_compressed_bytes_written() /
    //                        rg_writer->total_bytes_written()
    //             << std::endl
    //             << head << std::endl;

    if (rg_writer->total_bytes_written() &&
        rg_writer->total_compressed_bytes_written() +
                rg_writer->total_compressed_bytes() +
                estimated_bytes * rg_writer->total_compressed_bytes_written() /
                    rg_writer->total_bytes_written() >
            ROW_GROUP_SIZE) {
      // std::cerr << "row group written" << std::endl;
      // std::cerr << head << std::endl;
      rg_writer->Close();
      pq_writer->Close();

      file_id++;
      std::cerr << '\r' << file_id;
      PARQUET_ASSIGN_OR_THROW(outfile,
                              arrow::io::FileOutputStream::Open(
                                  std::to_string(file_id) + ".parquet"));
      pq_writer = parquet::ParquetFileWriter::Open(outfile, schema, wr_props);
      rg_writer = pq_writer->AppendBufferedRowGroup();
    }
  }
  // std::cerr << '\r' << 'w' << '\r';
  std::cerr << std::endl;

  pq_reader->Close();
  rg_writer->Close();
  pq_writer->Close();

  return 0;
}
