# -*- coding: utf-8 -*-
# Generated by the protocol buffer compiler.  DO NOT EDIT!
# source: webchela.proto
# Protobuf Python Version: 5.26.1
"""Generated protocol buffer code."""
from google.protobuf import descriptor as _descriptor
from google.protobuf import descriptor_pool as _descriptor_pool
from google.protobuf import symbol_database as _symbol_database
from google.protobuf.internal import builder as _builder
# @@protoc_insertion_point(imports)

_sym_db = _symbol_database.Default()




DESCRIPTOR = _descriptor_pool.Default().AddSerializedFile(b'\n\x0ewebchela.proto\x12\x08webchela\"#\n\x05\x43hunk\x12\r\n\x05\x63hunk\x18\x01 \x01(\x0c\x12\x0b\n\x03\x65nd\x18\x02 \x01(\x08\"\x07\n\x05\x45mpty\"9\n\x04Load\x12\x10\n\x08\x63pu_load\x18\x01 \x01(\x05\x12\x10\n\x08mem_free\x18\x02 \x01(\x03\x12\r\n\x05score\x18\x03 \x01(\x05\"\xd9\x01\n\x06Result\x12\x0c\n\x04UUID\x18\x01 \x01(\t\x12\x10\n\x08page_url\x18\x02 \x01(\t\x12\x12\n\npage_title\x18\x03 \x01(\t\x12\x11\n\tpage_body\x18\x04 \x01(\t\x12\x13\n\x0bscreenshots\x18\x05 \x03(\t\x12\x16\n\x0escreenshots_id\x18\x06 \x03(\x05\x12\x0f\n\x07scripts\x18\x07 \x03(\t\x12\x12\n\nscripts_id\x18\x08 \x03(\x05\x12\x0b\n\x03url\x18\t \x01(\t\x12\x13\n\x0bstatus_code\x18\n \x01(\x05\x12\x14\n\x0c\x63ontent_type\x18\x0b \x01(\t\"\xe6\x05\n\x04Task\x12\x11\n\tclient_id\x18\x01 \x01(\t\x12\x0c\n\x04urls\x18\x02 \x03(\t\x12\x0f\n\x07\x63ookies\x18\x03 \x03(\t\x12\x13\n\x0bscreenshots\x18\x04 \x03(\t\x12\x0f\n\x07scripts\x18\x05 \x03(\t\x12\x12\n\nchunk_size\x18\x06 \x01(\x03\x12\x10\n\x08\x63pu_load\x18\x07 \x01(\x05\x12\x10\n\x08mem_free\x18\x08 \x01(\x03\x12\x11\n\tpage_size\x18\t \x01(\x03\x12\x14\n\x0cpage_timeout\x18\n \x01(\x05\x12\x13\n\x0bretry_codes\x18\x0b \x03(\x05\x12\x19\n\x11retry_codes_tries\x18\x0c \x01(\x05\x12\x1a\n\x12screenshot_timeout\x18\r \x01(\x05\x12\x16\n\x0escript_timeout\x18\x0e \x01(\x05\x12\x0f\n\x07timeout\x18\x0f \x01(\x05\x12\x1a\n\x12tab_open_randomize\x18\x10 \x01(\t\x12\'\n\x07\x62rowser\x18\x11 \x01(\x0b\x32\x16.webchela.Task.Browser\x12#\n\x05\x64\x65\x62ug\x18\x12 \x01(\x0b\x32\x14.webchela.Task.Debug\x1a\x85\x01\n\x07\x42rowser\x12\x0c\n\x04type\x18\x01 \x01(\t\x12\x10\n\x08\x61rgument\x18\x02 \x03(\t\x12\x11\n\textension\x18\x03 \x03(\t\x12\x10\n\x08geometry\x18\x04 \x01(\t\x12\x10\n\x08instance\x18\x05 \x01(\x05\x12\x14\n\x0cinstance_tab\x18\x06 \x01(\x05\x12\r\n\x05proxy\x18\x07 \x01(\t\x1a\xbd\x01\n\x05\x44\x65\x62ug\x12\x17\n\x0fpre_close_delay\x18\x01 \x01(\x05\x12\x18\n\x10pre_cookie_delay\x18\x02 \x01(\x05\x12\x16\n\x0epre_open_delay\x18\x03 \x01(\x05\x12\x19\n\x11pre_process_delay\x18\x04 \x01(\x05\x12\x1c\n\x14pre_screenshot_delay\x18\x05 \x01(\x05\x12\x18\n\x10pre_script_delay\x18\x06 \x01(\x05\x12\x16\n\x0epre_wait_delay\x18\x07 \x01(\x05\x32\x66\n\x06Server\x12,\n\x07GetLoad\x12\x0f.webchela.Empty\x1a\x0e.webchela.Load\"\x00\x12.\n\x07RunTask\x12\x0e.webchela.Task\x1a\x0f.webchela.Chunk\"\x00\x30\x01\x42\x0cZ\n.;webchelab\x06proto3')

_globals = globals()
_builder.BuildMessageAndEnumDescriptors(DESCRIPTOR, _globals)
_builder.BuildTopDescriptorsAndMessages(DESCRIPTOR, 'webchela_pb2', _globals)
if not _descriptor._USE_C_DESCRIPTORS:
  _globals['DESCRIPTOR']._loaded_options = None
  _globals['DESCRIPTOR']._serialized_options = b'Z\n.;webchela'
  _globals['_CHUNK']._serialized_start=28
  _globals['_CHUNK']._serialized_end=63
  _globals['_EMPTY']._serialized_start=65
  _globals['_EMPTY']._serialized_end=72
  _globals['_LOAD']._serialized_start=74
  _globals['_LOAD']._serialized_end=131
  _globals['_RESULT']._serialized_start=134
  _globals['_RESULT']._serialized_end=351
  _globals['_TASK']._serialized_start=354
  _globals['_TASK']._serialized_end=1096
  _globals['_TASK_BROWSER']._serialized_start=771
  _globals['_TASK_BROWSER']._serialized_end=904
  _globals['_TASK_DEBUG']._serialized_start=907
  _globals['_TASK_DEBUG']._serialized_end=1096
  _globals['_SERVER']._serialized_start=1098
  _globals['_SERVER']._serialized_end=1200
# @@protoc_insertion_point(module_scope)
