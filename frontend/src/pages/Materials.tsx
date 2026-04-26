import { useState, useEffect, useCallback } from 'react';
import {
  Typography, Card, Upload, Button, Table, Tag, Space, Modal, Spin,
  Empty, message, Popconfirm, Select, Tabs,
} from 'antd';
import {
  InboxOutlined, FileTextOutlined,
  FilePdfOutlined, FileExcelOutlined, DeleteOutlined,
  EyeOutlined, ReloadOutlined,
} from '@ant-design/icons';
import type { UploadProps } from 'antd';
import api from '../services/api';

interface DocumentItem {
  id: string;
  filename: string;
  size: number;
  doc_type: string;
  project_id: string;
  parsed_length: number;
  chunks_indexed: number;
  metadata?: Record<string, unknown>;
  created_at?: string;
}

interface ProjectItem {
  id: string;
  name: string;
  company_name: string;
}

const { Dragger } = Upload;

const docTypeMap: Record<string, { color: string; label: string }> = {
  sample: { color: 'blue', label: '样本范文' },
  financial: { color: 'green', label: '财务数据' },
  patent: { color: 'orange', label: '知识产权' },
  contract: { color: 'purple', label: '产学研合同' },
  other: { color: 'default', label: '其他材料' },
};

function formatSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function getFileIcon(filename: string) {
  const ext = filename.split('.').pop()?.toLowerCase();
  if (ext === 'pdf') return <FilePdfOutlined style={{ color: '#ff4d4f' }} />;
  if (ext === 'xlsx' || ext === 'xls') return <FileExcelOutlined style={{ color: '#52c41a' }} />;
  return <FileTextOutlined />;
}

export default function Materials() {
  const [docs, setDocs] = useState<DocumentItem[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewDoc, setPreviewDoc] = useState<DocumentItem | null>(null);
  const [previewText, setPreviewText] = useState('');
  const [docType, setDocType] = useState('other');
  const [projectId, setProjectId] = useState('');
  const [activeTab, setActiveTab] = useState('all');
  const [projects, setProjects] = useState<ProjectItem[]>([]);

  const loadDocs = useCallback(async () => {
    setLoading(true);
    try {
      const params = projectId ? { project_id: projectId } : {};
      const resp = await api.get('/documents', { params });
      setDocs(resp.data || []);
    } catch {
      // Backend may not be running
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  const loadProjects = useCallback(async () => {
    try {
      const resp = await api.get('/projects');
      setProjects(resp.data || []);
    } catch {
      // Backend may not be running
    }
  }, []);

  useEffect(() => { loadDocs(); loadProjects(); }, [loadDocs, loadProjects]);

  const handleUpload = useCallback(async (file: File) => {
    setUploading(true);
    try {
      const formData = new FormData();
      formData.append('file', file);
      formData.append('doc_type', docType);
      formData.append('project_id', projectId);
      const resp = await api.post('/documents/upload', formData);
      message.success(
        `${file.name} 上传成功，已解析 ${resp.data.parsed_length} 字符` +
        (resp.data.chunks_indexed ? `，索引 ${resp.data.chunks_indexed} 个块` : '')
      );
      await loadDocs();
    } catch (err: unknown) {
      const msg = err && typeof err === 'object' && 'response' in err
        ? (err as { response: { data?: { detail?: string } } }).response?.data?.detail
        : undefined;
      message.error(msg || '上传失败');
    } finally {
      setUploading(false);
    }
    return false; // Prevent default upload behavior
  }, [docType, projectId, loadDocs]);

  const uploadProps: UploadProps = {
    name: 'file',
    multiple: true,
    showUploadList: false,
    beforeUpload: handleUpload,
    accept: '.pdf,.docx,.doc,.xlsx,.xls,.txt,.md,.csv,.html',
  };

  const handlePreview = async (doc: DocumentItem) => {
    setPreviewDoc(doc);
    setPreviewOpen(true);
    try {
      const resp = await api.get(`/documents/${doc.id}`);
      setPreviewText(resp.data.parsed_text || '');
    } catch {
      setPreviewText('无法加载文档内容');
    }
  };

  const handleDelete = async (doc: DocumentItem) => {
    try {
      await api.delete(`/documents/${doc.id}?project_id=${doc.project_id || ''}`);
      message.success(`${doc.filename} 已删除`);
      await loadDocs();
    } catch {
      message.error('删除失败');
    }
  };

  const filteredDocs = activeTab === 'all'
    ? docs
    : docs.filter((d) => d.doc_type === activeTab);

  const columns = [
    {
      title: '文件名',
      dataIndex: 'filename',
      key: 'filename',
      render: (name: string) => (
        <Space>
          {getFileIcon(name)}
          <span>{name}</span>
        </Space>
      ),
    },
    {
      title: '大小',
      dataIndex: 'size',
      key: 'size',
      width: 100,
      render: (s: number) => formatSize(s),
    },
    {
      title: '类型',
      dataIndex: 'doc_type',
      key: 'doc_type',
      width: 120,
      render: (t: string) => (
        <Tag color={docTypeMap[t]?.color}>{docTypeMap[t]?.label || t}</Tag>
      ),
    },
    {
      title: '解析字符',
      dataIndex: 'parsed_length',
      key: 'parsed_length',
      width: 100,
      render: (l: number) => l ? l.toLocaleString() : '-',
    },
    {
      title: '操作',
      key: 'actions',
      width: 160,
      render: (_: unknown, record: DocumentItem) => (
        <Space>
          <Button size="small" icon={<EyeOutlined />} onClick={() => handlePreview(record)}>
            预览
          </Button>
          <Popconfirm title="确定删除此文档？" onConfirm={() => handleDelete(record)}>
            <Button size="small" danger icon={<DeleteOutlined />} />
          </Popconfirm>
        </Space>
      ),
    },
  ];

  return (
    <div>
      <Typography.Title level={3}>材料库</Typography.Title>

      <Card style={{ marginBottom: 16 }}>
        <Space style={{ width: '100%', justifyContent: 'space-between' }} wrap>
          <Space>
            <span>文档类型：</span>
            <Select
              value={docType}
              onChange={setDocType}
              options={Object.entries(docTypeMap).map(([k, v]) => ({ value: k, label: v.label }))}
              style={{ width: 140 }}
            />
            <span>关联项目：</span>
            <Select
              value={projectId}
              onChange={setProjectId}
              allowClear
              placeholder="全部项目"
              options={projects.map((p) => ({ value: p.id, label: `${p.company_name || p.name}` }))}
              style={{ width: 260 }}
            />
          </Space>
          <Button onClick={loadDocs} loading={loading} icon={<ReloadOutlined />}>刷新</Button>
        </Space>
      </Card>

      <Card>
        <Dragger {...uploadProps} style={{ marginBottom: 24 }}>
          <p className="ant-upload-drag-icon">
            <InboxOutlined />
          </p>
          <p className="ant-upload-text">点击或拖拽文件到此区域上传</p>
          <p className="ant-upload-hint">
            支持 PDF、Word (.docx)、Excel (.xlsx)、TXT、Markdown、HTML 格式
          </p>
        </Dragger>

        {uploading && <Spin tip="正在上传并解析..." style={{ display: 'block', textAlign: 'center', marginBottom: 16 }} />}

        <Tabs
          activeKey={activeTab}
          onChange={setActiveTab}
          items={[
            { key: 'all', label: '全部' },
            ...Object.entries(docTypeMap).map(([k, v]) => ({
              key: k,
              label: v.label,
            })),
          ]}
        />

        <Table
          dataSource={filteredDocs}
          columns={columns}
          rowKey="id"
          loading={loading}
          locale={{ emptyText: <Empty description="暂无材料，上传文件开始" /> }}
          pagination={{ pageSize: 20 }}
        />
      </Card>

      <Modal
        title={previewDoc?.filename || '文档预览'}
        open={previewOpen}
        onCancel={() => { setPreviewOpen(false); setPreviewText(''); }}
        footer={null}
        width={800}
      >
        <div style={{
          maxHeight: 500,
          overflow: 'auto',
          whiteSpace: 'pre-wrap',
          fontFamily: 'monospace',
          fontSize: 13,
          lineHeight: 1.8,
          background: '#fafafa',
          padding: 16,
          borderRadius: 8,
        }}>
          {previewText || '加载中...'}
        </div>
      </Modal>
    </div>
  );
}
