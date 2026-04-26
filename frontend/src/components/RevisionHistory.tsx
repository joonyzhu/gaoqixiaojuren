import { useState, useEffect, useCallback } from 'react';
import { Timeline, Button, Modal, Typography, Spin, Empty, message, Space } from 'antd';
import { HistoryOutlined, RollbackOutlined } from '@ant-design/icons';
import api from '../services/api';

interface Revision {
  id: string;
  section_id: string;
  version: number;
  content: string;
  model_used: string;
  created_at: string;
}

interface Props {
  projectId: string;
  sectionId: string;
  onRestore: (content: string) => void;
}

export default function RevisionHistory({ projectId, sectionId, onRestore }: Props) {
  const [revisions, setRevisions] = useState<Revision[]>([]);
  const [loading, setLoading] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewContent, setPreviewContent] = useState('');
  const [previewTitle, setPreviewTitle] = useState('');

  const load = useCallback(async () => {
    if (!projectId || !sectionId) return;
    setLoading(true);
    try {
      const resp = await api.get(`/projects/${projectId}/revisions/${sectionId}`);
      setRevisions(resp.data || []);
    } catch {
      // Backend may not be ready
    } finally {
      setLoading(false);
    }
  }, [projectId, sectionId]);

  useEffect(() => { load(); }, [load]);

  const handlePreview = (rev: Revision) => {
    setPreviewTitle(`版本 ${rev.version} — ${new Date(rev.created_at).toLocaleString('zh-CN')}`);
    setPreviewContent(rev.content);
    setPreviewOpen(true);
  };

  const handleRestore = (rev: Revision) => {
    onRestore(rev.content);
    message.success(`已恢复到版本 ${rev.version}`);
    setPreviewOpen(false);
  };

  return (
    <div>
      {loading ? <Spin /> : (
        revisions.length === 0 ? (
          <Empty description="暂无修订历史，点击 AI 生成后将自动记录" />
        ) : (
          <Timeline
            items={revisions.map((rev) => ({
              color: rev.version === 1 ? 'green' : 'blue',
              dot: rev.version === 1 ? <HistoryOutlined /> : undefined,
              children: (
                <div>
                  <Typography.Text strong>版本 {rev.version}</Typography.Text>
                  <Typography.Text type="secondary" style={{ marginLeft: 8, fontSize: 12 }}>
                    {new Date(rev.created_at).toLocaleString('zh-CN')}
                  </Typography.Text>
                  {rev.model_used && (
                    <Typography.Text type="secondary" style={{ marginLeft: 8, fontSize: 11 }}>
                      模型: {rev.model_used}
                    </Typography.Text>
                  )}
                  <br />
                  <Space size={4} style={{ marginTop: 4 }}>
                    <Button size="small" type="link" onClick={() => handlePreview(rev)}>
                      查看
                    </Button>
                    {rev.version !== 1 && (
                      <Button
                        size="small"
                        type="link"
                        icon={<RollbackOutlined />}
                        onClick={() => handleRestore(rev)}
                      >
                        恢复此版本
                      </Button>
                    )}
                  </Space>
                </div>
              ),
            }))}
          />
        )
      )}

      <Modal
        title={previewTitle}
        open={previewOpen}
        onCancel={() => setPreviewOpen(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewOpen(false)}>关闭</Button>,
          <Button
            key="restore"
            type="primary"
            icon={<RollbackOutlined />}
            onClick={() => {
              onRestore(previewContent);
              setPreviewOpen(false);
            }}
          >
            恢复此版本
          </Button>,
        ]}
        width={800}
      >
        <div style={{
          maxHeight: 500,
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
          fontFamily: '"PingFang SC", "Microsoft YaHei", serif',
          fontSize: 14,
          lineHeight: 2,
          background: '#fafafa',
          padding: 16,
          borderRadius: 8,
        }}>
          {previewContent}
        </div>
      </Modal>
    </div>
  );
}
