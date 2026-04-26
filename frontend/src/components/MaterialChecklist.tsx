import { useState } from 'react';
import {
  Card, Progress, Button, Upload, Tag, Space, Typography, message, Collapse,
} from 'antd';
import {
  CheckCircleOutlined, ExclamationCircleOutlined,
  UploadOutlined, LoadingOutlined, PlayCircleOutlined,
} from '@ant-design/icons';
import api from '../services/api';

interface ChecklistItem {
  id: string;
  category: string;
  item: string;
  required: boolean;
  description: string;
  uploaded: boolean;
  doc_ids: string[];
}

interface ChecklistStats {
  total_items: number;
  required_items: number;
  completed_items: number;
  required_completed: number;
  completion_pct: number;
  all_required_done: boolean;
}

interface Props {
  projectId: string;
  checklist: ChecklistItem[];
  stats: ChecklistStats;
  onStartWriting: () => void;
  onRefresh: () => void;
}

export default function MaterialChecklist({ projectId, checklist, stats, onStartWriting, onRefresh }: Props) {
  const [uploading, setUploading] = useState<string | null>(null);

  const handleUpload = async (itemId: string, file: File) => {
    setUploading(itemId);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('project_id', projectId);
      formData.append('checklist_item_id', itemId);
      formData.append('doc_type', 'other');
      await api.post('/documents/upload', formData);
      message.success(`${file.name} 上传成功，已关联到材料清单`);
      onRefresh();
    } catch {
      message.error('上传失败');
    } finally {
      setUploading(null);
    }
    return false;
  };

  const categories = [...new Set(checklist.map((i) => i.category))];

  return (
    <div>
      <Card style={{ marginBottom: 16 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }} wrap>
          <Space direction="vertical" size={4}>
            <Typography.Title level={4} style={{ margin: 0 }}>材料收集</Typography.Title>
            <Typography.Text type="secondary">
              请上传申报所需的材料
            </Typography.Text>
          </Space>
          <Space direction="vertical" align="end">
            <Progress
              percent={stats.completion_pct}
              status={stats.all_required_done ? 'success' : 'active'}
              format={() => `${stats.completed_items}/${stats.total_items}`}
              style={{ width: 200 }}
            />
            {stats.required_items > 0 && (
              <Typography.Text type="secondary">
                必传项：{stats.required_completed}/{stats.required_items}
              </Typography.Text>
            )}
          </Space>
        </Space>
      </Card>

      <Collapse
        defaultActiveKey={categories}
        items={categories.map((cat) => {
          const items = checklist.filter((i) => i.category === cat);
          const catDone = items.filter((i) => i.uploaded).length;
          return {
            key: cat,
            label: (
              <Space>
                <span>{cat}</span>
                <Tag color={catDone === items.length ? 'success' : 'processing'}>
                  {catDone}/{items.length}
                </Tag>
              </Space>
            ),
            children: (
              <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
                {items.map((item) => (
                  <Card
                    key={item.id}
                    size="small"
                    style={{
                      borderLeft: item.required && !item.uploaded
                        ? '3px solid #ff4d4f'
                        : item.uploaded
                        ? '3px solid #52c41a'
                        : '3px solid #d9d9d9',
                    }}
                  >
                    <Space style={{ width: '100%', justifyContent: 'space-between' }}>
                      <Space>
                        {item.uploaded ? (
                          <CheckCircleOutlined style={{ color: '#52c41a' }} />
                        ) : item.required ? (
                          <ExclamationCircleOutlined style={{ color: '#ff4d4f' }} />
                        ) : (
                          <ExclamationCircleOutlined style={{ color: '#d9d9d9' }} />
                        )}
                        <div>
                          <Typography.Text strong={item.required}>
                            {item.required ? <Tag color="error" style={{ fontSize: 10, marginRight: 4 }}>必传</Tag> : null}
                            {item.item}
                          </Typography.Text>
                          <br />
                          <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                            {item.description}
                          </Typography.Text>
                          {item.uploaded && item.doc_ids?.length > 0 && (
                            <Tag color="success" style={{ marginLeft: 8, fontSize: 11 }}>
                              {item.doc_ids.length} 个文件
                            </Tag>
                          )}
                        </div>
                      </Space>
                      <Upload
                        showUploadList={false}
                        beforeUpload={(file) => handleUpload(item.id, file)}
                        accept=".pdf,.docx,.doc,.xlsx,.xls,.txt,.md,.csv,.html"
                      >
                        <Button
                          size="small"
                          icon={uploading === item.id ? <LoadingOutlined /> : <UploadOutlined />}
                          type={item.uploaded ? 'default' : 'primary'}
                          ghost={item.uploaded}
                        >
                          {item.uploaded ? '补充' : '上传'}
                        </Button>
                      </Upload>
                    </Space>
                  </Card>
                ))}
              </div>
            ),
          };
        })}
      />

      <div style={{ textAlign: 'center', marginTop: 24 }}>
        <Button
          type="primary"
          size="large"
          icon={<PlayCircleOutlined />}
          onClick={onStartWriting}
        >
          开始 AI 撰写
        </Button>
      </div>
    </div>
  );
}
