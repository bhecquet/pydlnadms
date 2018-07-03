import os
from ..dlna import *
from ..http import *

from backend.pydlnadms.dlna import TIMESEEKRANGE_DLNA_ORG, CONTENTFEATURES_DLNA_ORG,\
    DLNAContentFeatures
from backend.pydlnadms.http import HTTPRangeField, HTTPRange
import logging
from backend.pydlnadms.resources import FileResource
from backend.pydlnadms.fileManagement.Tools import guessMimetype

pydlnaFile = os.path.expanduser("~") + os.sep + '.pydlna'
from backend.pydlnadms.server import setServerActive

def dlna_npt_to_seconds(npt_time):
    import datetime
    if ':' in npt_time:
        hours, mins, secs = map(float, npt_time.split(':'))
        return datetime.timedelta(hours=hours, minutes=mins, seconds=secs).total_seconds()
    else:
        return float(npt_time)

def transcode_resource(context):
    request = context.request
    if TIMESEEKRANGE_DLNA_ORG in request:
        ranges_field = HTTPRangeField.from_string(request[TIMESEEKRANGE_DLNA_ORG])
    else:
        ranges_field = HTTPRangeField({'npt': HTTPRange()})
    npt_range = ranges_field['npt']
    npt_range.size = '*'
    context.start_response(206, [
        (CONTENTFEATURES_DLNA_ORG, DLNAContentFeatures(
            support_time_seek=True,
            transcoded=True)),
        ('Ext', None),
        ('transferMode.dlna.org', 'Streaming'),
        (TIMESEEKRANGE_DLNA_ORG, HTTPRangeField({'npt': npt_range})),
        ('Content-Type', 'video/mpeg'),])
    start = npt_range.start
    end = npt_range.end
    transcoder_args = [
        './transcode',
        request.query['path'][-1],
        str(dlna_npt_to_seconds(start)) if start else start,
        str(dlna_npt_to_seconds(end)) if end else end]
    import subprocess, os
    try:
        subprocess.check_call(
            transcoder_args,
            stdin=open(os.devnull, 'rb'),
            stdout=context.socket,
            close_fds=True)
    except subprocess.CalledProcessError as exc:
        logging.warning('Transcoder error: %s', exc)

def thumbnail_resource(context):
    import subprocess, os
#    with subprocess.Popen([
#                    'ffmpegthumbnailer',
#                    '-i', context.request.query['path'][-1],
#                    '-o', '/dev/stdout',
#                    '-c', 'jpeg',],
#                stdin=open(os.devnull, 'rb'),
#                # ffmpegthumbnailer fails if stdout is a socket
#                # Error: Failed to open output file: /dev/stdout
#                stdout=subprocess.PIPE,
#                stderr=None,
#                close_fds=True
#            ) as process:
#        context.start_response(206, [
#                ('Content-Type', 'image/jpeg'),
#                ('Ext', None),
#                ('transferMode.dlna.org', 'Streaming'),
#                (CONTENTFEATURES_DLNA_ORG, DLNAContentFeatures()),
#            ])
#        while True:
#            buf = process.stdout.read(0x10000)
#            if not buf:
#                break
#            context.socket.sendall(buf)

def head_file_resource(context):
    request = context.request
    path = request.query['path'][-1]

    resource = FileResource(path, 0, None)
    response_headers = [
        ('Content-Type', guessMimetype(path)),
        ('Content-Length', resource.size),
        ('transferMode.dlna.org', 'Streaming'),
        ('Accept-Ranges', 'bytes'),
        ('Connection', 'close'),
        ('Ext', None),
        ('realTimeInfo.dlna.org', 'DLNA.ORG_TLAG=*'),
        ('contentFeatures.dlna.org', 'DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000'),
#         (CONTENTFEATURES_DLNA_ORG, DLNAContentFeatures(support_range=True)),

        ]
    context.start_response(200, response_headers)
 
def file_resource(context):
    request = context.request
    path = request.query['path'][-1]
#     print(path)
    if 'Range' in request:
        ranges_field = HTTPRangeField.from_string(request['Range'])
        seek = 'range'
    elif TIMESEEKRANGE_DLNA_ORG in request:
        ranges_field = HTTPRangeField.from_string(request[TIMESEEKRANGE_DLNA_ORG])
        seek = 'time'
    else:
        ranges_field = HTTPRangeField({'bytes': HTTPRange()})
        seek = 'range'
    
    if seek == 'range':
        bytes_range = ranges_field['bytes']
        resource = FileResource(
            path,
            int(bytes_range.start) if bytes_range.start else 0,
            int(bytes_range.end) + 1 if bytes_range.end else None)
        bytes_range.size = resource.size
        response_headers = [
#             ('Content-Range', HTTPRangeField({'bytes': bytes_range})),
            ('Accept-Ranges', 'bytes'),
            ('Content-Type', guessMimetype(path)),
            (CONTENTFEATURES_DLNA_ORG, DLNAContentFeatures(support_range=True)),
            ('Ext', None),
            ('transferMode.dlna.org', 'Streaming'),
            
            ('Content-Range', '0-%s/%s' % (resource.size-1, resource.size)),
            ('Content-Length', resource.size),
            ('Connection', 'close'),
            ('realTimeInfo.dlna.org', 'DLNA.ORG_TLAG=*'),
            ('contentFeatures.dlna.org', 'DLNA.ORG_OP=01;DLNA.ORG_CI=0;DLNA.ORG_FLAGS=01700000000000000000000000000000'),
            ]
        if resource.length:
            response_headers.append(('Content-Length', resource.length))
        context.start_response(206, response_headers)
        
        if request.method == 'GET':
            import socket, errno
            while True:
                data = resource.read(0x10000)
                if not data:
                    break
                try:
                    context.socket.sendall(data)
                    mark_active()
                except socket.error as exc:
                    if exc.errno == errno.EPIPE:
                        break
                
    elif seek == 'time':
        fileBitrate = FileResource.getBitrate(path)
        npt_range = ranges_field['npt']
        npt_range.size = '*'
        context.start_response(206, [
            (CONTENTFEATURES_DLNA_ORG, DLNAContentFeatures(
                support_time_seek=True,
                transcoded=False)),
            ('Ext', None),
            ('transferMode.dlna.org', 'Streaming'),
            (TIMESEEKRANGE_DLNA_ORG, HTTPRangeField({'npt': npt_range})),
            ('Content-Type', guessMimetype(path)),])
        start = npt_range.start
        end = npt_range.end
        
        resource = FileResource(
            path,
            int(dlna_npt_to_seconds(start) * fileBitrate) if start else 0,
            int(dlna_npt_to_seconds(end) * fileBitrate) if end else None)

        if request.method == 'GET':
            import socket, errno
            while True:
                data = resource.read(0x10000)
                if not data:
                    break
                try:
                    context.socket.sendall(data)
                    mark_active()
                except socket.error as exc:
                    if exc.errno == errno.EPIPE:
                        break
        
def mark_active():
    setServerActive()
    open(pydlnaFile, 'w').close()


