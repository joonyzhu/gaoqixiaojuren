import { useState, useEffect, useCallback } from 'react';
import { List, Input, Button, Space, Typography, Checkbox, Popconfirm, message } from 'antd';
import { CheckCircleOutlined, DeleteOutlined, CommentOutlined } from '@ant-design/icons';
import api from '../services/api';

interface Comment {
  id: string;
  section_id: string;
  content: string;
  author: string;
  resolved: boolean;
  created_at: string;
}

interface Props {
  projectId: string;
  sectionId: string;
}

export default function SectionComments({ projectId, sectionId }: Props) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [loading, setLoading] = useState(false);
  const [newComment, setNewComment] = useState('');

  const loadComments = useCallback(async () => {
    if (!projectId || !sectionId) return;
    setLoading(true);
    try {
      const resp = await api.get(`/projects/${projectId}/comments?section_id=${sectionId}`);
      setComments(resp.data || []);
    } catch {
      // Backend may not be ready
    } finally {
      setLoading(false);
    }
  }, [projectId, sectionId]);

  useEffect(() => { loadComments(); }, [loadComments]);

  const handleAdd = async () => {
    if (!newComment.trim()) return;
    try {
      await api.post(`/projects/${projectId}/comments`, {
        section_id: sectionId,
        content: newComment.trim(),
      });
      message.success('评论已添加');
      setNewComment('');
      loadComments();
    } catch {
      message.error('添加评论失败');
    }
  };

  const handleToggleResolve = async (commentId: string, resolved: boolean) => {
    try {
      await api.patch(`/projects/${projectId}/comments/${commentId}`, { resolved: !resolved });
      loadComments();
    } catch {
      message.error('操作失败');
    }
  };

  const handleDelete = async (commentId: string) => {
    try {
      await api.delete(`/projects/${projectId}/comments/${commentId}`);
      loadComments();
    } catch {
      message.error('删除失败');
    }
  };

  const unresolvedCount = comments.filter((c) => !c.resolved).length;

  return (
    <div>
      {unresolvedCount > 0 && (
        <Typography.Text type="warning" style={{ marginBottom: 8, display: 'block' }}>
          <CommentOutlined /> {unresolvedCount} 条未解决评论
        </Typography.Text>
      )}
      <List
        loading={loading}
        dataSource={comments}
        locale={{ emptyText: '暂无评论' }}
        renderItem={(c) => (
          <List.Item
            actions={[
              <Checkbox
                key="resolve"
                checked={c.resolved}
                onChange={() => handleToggleResolve(c.id, c.resolved)}
              >
                {c.resolved ? '已解决' : '解决'}
              </Checkbox>,
              <Popconfirm key="del" title="删除此评论？" onConfirm={() => handleDelete(c.id)}>
                <Button size="small" type="text" danger icon={<DeleteOutlined />} />
              </Popconfirm>,
            ]}
          >
            <List.Item.Meta
              title={
                <Space>
                  <Typography.Text strong>{c.author}</Typography.Text>
                  <Typography.Text type="secondary" style={{ fontSize: 12 }}>
                    {new Date(c.created_at).toLocaleString('zh-CN')}
                  </Typography.Text>
                  {c.resolved && <CheckCircleOutlined style={{ color: '#52c41a' }} />}
                </Space>
              }
              description={
                <Typography.Text style={{
                  textDecoration: c.resolved ? 'line-through' : 'none',
                  color: c.resolved ? '#999' : '#333',
                }}>
                  {c.content}
                </Typography.Text>
              }
            />
          </List.Item>
        )}
      />
      <Space.Compact style={{ width: '100%', marginTop: 12 }}>
        <Input
          placeholder="添加修改意见..."
          value={newComment}
          onChange={(e) => setNewComment(e.target.value)}
          onPressEnter={handleAdd}
        />
        <Button type="primary" onClick={handleAdd} icon={<CommentOutlined />}>
          添加
        </Button>
      </Space.Compact>
    </div>
  );
}
