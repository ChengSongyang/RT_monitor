#!/usr/bin/env python3
"""
数据API服务器 - 提供放射治疗新闻和论文数据（SQLite版）
"""
import json
import os
import sys
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime
import urllib.parse

# 将 scripts 目录加入 sys.path 以便导入 db 模块
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from db import init_db, query_content, get_report, log_sync, query_rss_sources, query_sources, query_stats


class APIHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        """处理GET请求"""
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path
        query = urllib.parse.parse_qs(parsed_path.query)

        # 设置CORS头
        self.send_response(200)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

        # 路由处理
        if path == '/api/items':
            category = query.get('category', [None])[0]
            source = query.get('source', [None])[0]
            source_type = query.get('source_type', [None])[0]
            source_id = query.get('source_id', [None])[0]
            source_kind = query.get('source_kind', [None])[0]
            search = query.get('search', [None])[0]
            is_featured_str = query.get('is_featured', [None])[0]
            is_featured = None
            if is_featured_str is not None:
                is_featured = is_featured_str.lower() in ('true', '1', 'yes')
            limit = int(query.get('limit', [20])[0])
            page = int(query.get('page', [1])[0])

            data = query_content(
                category=category,
                source=source,
                source_type=source_type,
                source_id=source_id,
                source_kind=source_kind,
                search=search,
                is_featured=is_featured,
                page=page,
                limit=limit,
            )
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

        elif path == '/api/papers':
            limit = int(query.get('limit', [50])[0])
            page = int(query.get('page', [1])[0])
            data = query_content(source_type='paper', page=page, limit=limit)
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

        elif path == '/api/news':
            limit = int(query.get('limit', [50])[0])
            page = int(query.get('page', [1])[0])
            data = query_content(source_type='news', page=page, limit=limit)
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

        elif path == '/api/sources':
            view = query.get('view', [None])[0]
            if view == 'rss':
                data = query_rss_sources()
                self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))
                return

            source_kind = query.get('kind', [None])[0] or query.get('source_kind', [None])[0]
            include_empty_str = query.get('include_empty', ['true'])[0]
            include_empty = include_empty_str.lower() not in ('false', '0', 'no')
            data = query_sources(source_kind=source_kind, include_empty=include_empty)
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

        elif path == '/api/rss-sources':
            data = query_rss_sources()
            self.wfile.write(json.dumps(data, ensure_ascii=False).encode('utf-8'))

        elif path.startswith('/api/reports/'):
            content_id = path[len('/api/reports/'):]
            report = get_report(content_id)
            if report:
                self.wfile.write(json.dumps(report, ensure_ascii=False).encode('utf-8'))
            else:
                self.wfile.write(json.dumps({'error': 'Report not found'}).encode('utf-8'))

        elif path == '/api/stats':
            self.wfile.write(json.dumps(query_stats(), ensure_ascii=False).encode('utf-8'))

        else:
            # 404
            self.send_response(404)
            self.end_headers()
            self.wfile.write(json.dumps({'error': 'Not found'}).encode('utf-8'))

    def do_POST(self):
        """处理POST请求"""
        if self.path == '/api/refresh':
            content_length = int(self.headers.get('Content-Length', 0))
            post_data = self.rfile.read(content_length)

            try:
                from collect import collect_all
                result = collect_all()
                log_sync('api_refresh', result.get('found', 0),
                         result.get('new', 0), result.get('updated', 0))

                self.send_response(200)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({
                    'success': True,
                    'found': result.get('found', 0),
                    'new': result.get('new', 0),
                    'updated': result.get('updated', 0),
                }, ensure_ascii=False).encode('utf-8'))

            except Exception as e:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json; charset=utf-8')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({'error': str(e)}).encode('utf-8'))

        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        """处理OPTIONS请求（CORS预检）"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """自定义日志格式"""
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {args[0]}", file=sys.stderr)


def main():
    """启动API服务器"""
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8001

    # 确保数据库 schema 存在
    init_db()

    server = HTTPServer(('0.0.0.0', port), APIHandler)
    print(f"API server started on http://localhost:{port}", file=sys.stderr)
    print(f"Endpoints:", file=sys.stderr)
    print(f"   GET /api/items - List items (supports filtering)", file=sys.stderr)
    print(f"   GET /api/papers - List papers", file=sys.stderr)
    print(f"   GET /api/news - List news", file=sys.stderr)
    print(f"   GET /api/sources - Source catalog and coverage", file=sys.stderr)
    print(f"   GET /api/rss-sources - RSS source status", file=sys.stderr)
    print(f"   GET /api/stats - Statistics", file=sys.stderr)
    print(f"   GET /api/reports/<content_id> - Get report", file=sys.stderr)
    print(f"   POST /api/refresh - Refresh data", file=sys.stderr)

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped", file=sys.stderr)
        server.shutdown()


if __name__ == "__main__":
    main()
