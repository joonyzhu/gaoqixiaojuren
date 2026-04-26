import { useState, useEffect } from 'react';
import { Spin, Empty } from 'antd';
import api from '../services/api';

interface Props {
  projectId: string;
}

export default function DocumentPreview({ projectId }: Props) {
  const [html, setHtml] = useState('');
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (!projectId) return;
    setLoading(true);
    api.get(`/engine/preview/${projectId}`)
      .then((r) => setHtml(r.data.html))
      .catch(() => setHtml(''))
      .finally(() => setLoading(false));
  }, [projectId]);

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 40 }}><Spin tip="正在生成预览..." /></div>;
  }

  if (!html) {
    return <Empty description="暂无内容可供预览" />;
  }

  return (
    <div style={{
      background: '#e8e8e8',
      padding: 24,
      minHeight: 400,
    }}>
      <div
        style={{
          maxWidth: 800,
          margin: '0 auto',
          background: '#fff',
          boxShadow: '0 2px 12px rgba(0,0,0,0.15)',
          padding: '60px 72px',
          fontFamily: '"PingFang SC", "Microsoft YaHei", "SimSun", serif',
          fontSize: 14,
          lineHeight: 2,
          color: '#333',
        }}
        dangerouslySetInnerHTML={{ __html: html }}
      />
      <style>{`
        .preview-page h1 { font-size: 22pt; font-family: "SimHei", "PingFang SC", sans-serif; text-align: center; margin-bottom: 8px; }
        .preview-page h2 { font-size: 14pt; font-family: "KaiTi", "PingFang SC", serif; text-align: center; font-weight: normal; margin-bottom: 24px; }
        .preview-page h3 { font-size: 14pt; font-family: "SimHei", "PingFang SC", sans-serif; margin-top: 24px; margin-bottom: 12px; }
        .preview-page p { text-indent: 2em; margin-bottom: 4px; font-family: "SimSun", "PingFang SC", serif; }
        .preview-footer { margin-top: 32px; text-align: right; font-size: 12px; color: #999; border-top: 1px solid #eee; padding-top: 8px; }
      `}</style>
    </div>
  );
}
