import { useState, useEffect, useCallback } from 'react';
import {
  Card, Button, Modal, Form, Input, Select, Space, Typography, Tag,
  Spin, Descriptions, Alert, message, Popconfirm,
} from 'antd';
import {
  PlusOutlined, FileTextOutlined, SearchOutlined,
  LoadingOutlined, DeleteOutlined, FolderOpenOutlined,
  ReloadOutlined,
} from '@ant-design/icons';
import { useNavigate } from 'react-router-dom';
import api from '../services/api';

interface Project {
  id: string;
  name: string;
  project_type: 'gaoxin' | 'xiaojuren';
  status: string;
  phase: string;
  company_name: string;
  company_info: Record<string, unknown>;
  material_checklist: Array<{ required: boolean; uploaded: boolean }>;
  updated_at: string;
}

interface CompanyInfo {
  found: boolean;
  name: string;
  legal_representative?: string;
  registered_capital?: string;
  established_date?: string;
  business_status?: string;
  unified_code?: string;
  company_type?: string;
  industry?: string;
  business_scope?: string;
  address?: string;
  source?: string;
  message?: string;
}

const statusMap: Record<string, { color: string; label: string }> = {
  draft: { color: 'default', label: '材料收集' },
  generating: { color: 'processing', label: 'AI撰写中' },
  review: { color: 'warning', label: '人工审核' },
  done: { color: 'success', label: '已定稿' },
};

const phaseMap: Record<string, { color: string; label: string }> = {
  materials: { color: 'default', label: '收集中' },
  writing: { color: 'processing', label: '撰写中' },
  review: { color: 'warning', label: '审核中' },
  done: { color: 'success', label: '已完成' },
};

const typeMap: Record<string, string> = { gaoxin: '高新技术企业', xiaojuren: '专精特新小巨人' };

export default function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);
  const [form] = Form.useForm();
  const navigate = useNavigate();
  const [searching, setSearching] = useState(false);
  const [companyInfo, setCompanyInfo] = useState<CompanyInfo | null>(null);
  const [searchError, setSearchError] = useState('');
  const [creating, setCreating] = useState(false);

  const loadProjects = useCallback(async () => {
    setLoading(true);
    try {
      const resp = await api.get('/projects');
      setProjects(resp.data || []);
    } catch {
      // Backend may not be running
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { loadProjects(); }, [loadProjects]);

  const handleSearchCompany = useCallback(async () => {
    const companyName = form.getFieldValue('company_name')?.trim();
    if (!companyName || companyName.length < 2) return;

    setSearching(true);
    setSearchError('');
    setCompanyInfo(null);

    try {
      const resp = await api.post('/projects/enrich-company', { company_name: companyName });
      const data = resp.data;
      if (data.found) {
        setCompanyInfo(data);
        message.success(`已从${data.source || '公开渠道'}获取企业信息`);
      } else {
        setSearchError(data.message || '未找到企业信息，请手动填写');
      }
    } catch {
      setSearchError('搜索失败，请检查网络或手动填写');
    } finally {
      setSearching(false);
    }
  }, [form]);

  const handleCreate = async () => {
    try {
      const values = await form.validateFields();
      setCreating(true);
      const resp = await api.post('/projects', values);
      const project = resp.data;
      setOpen(false);
      form.resetFields();
      setCompanyInfo(null);
      setSearchError('');
      await loadProjects();
      navigate(`/project/${project.id}`);
    } catch (err: unknown) {
      const isValidationErr = err && typeof err === 'object' && 'errorFields' in err;
      if (!isValidationErr) message.error('创建失败，请检查后端是否启动');
    } finally {
      setCreating(false);
    }
  };

  const handleDelete = async (projectId: string, e?: React.MouseEvent) => {
    e?.stopPropagation();
    try {
      await api.delete(`/projects/${projectId}`);
      message.success('已删除');
      await loadProjects();
    } catch {
      message.error('删除失败');
    }
  };

  const handleClose = () => {
    setOpen(false);
    form.resetFields();
    setCompanyInfo(null);
    setSearchError('');
  };

  return (
    <div>
      <Space style={{ marginBottom: 24, justifyContent: 'space-between', width: '100%' }}>
        <Typography.Title level={3} style={{ margin: 0 }}>项目总览</Typography.Title>
        <Space>
          <Button onClick={loadProjects} loading={loading} icon={<ReloadOutlined />}>刷新</Button>
          <Button type="primary" icon={<PlusOutlined />} onClick={() => setOpen(true)}>
            新建项目
          </Button>
        </Space>
      </Space>

      {loading ? (
        <div style={{ textAlign: 'center', padding: 60 }}><Spin /></div>
      ) : projects.length === 0 ? (
        <Card style={{ textAlign: 'center', padding: 60 }}>
          <FileTextOutlined style={{ fontSize: 48, color: '#d9d9d9' }} />
          <p style={{ color: '#999', marginTop: 16 }}>暂无项目，点击上方按钮创建第一个申报项目</p>
        </Card>
      ) : (
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 16 }}>
          {projects.map((p) => (
            <Card
              key={p.id}
              hoverable
              onClick={() => navigate(`/project/${p.id}`)}
              title={p.name}
              extra={<Tag color={phaseMap[p.phase]?.color || statusMap[p.status]?.color}>{phaseMap[p.phase]?.label || statusMap[p.status]?.label}</Tag>}
              actions={[
                <FolderOpenOutlined key="open" onClick={() => navigate(`/project/${p.id}`)} />,
                <Popconfirm
                  key="delete"
                  title="确定删除此项目？所有相关材料将被删除。"
                  onConfirm={(e) => handleDelete(p.id, e as unknown as React.MouseEvent)}
                >
                  <DeleteOutlined />
                </Popconfirm>,
              ]}
            >
              <p><strong>企业：</strong>{p.company_name || '未填写'}</p>
              <p><strong>类型：</strong>{typeMap[p.project_type]}</p>
              {p.material_checklist?.length > 0 && (
                <p style={{ fontSize: 12, color: '#888' }}>
                  材料：{p.material_checklist.filter((i: { uploaded: boolean }) => i.uploaded).length}/{p.material_checklist.length}
                  {p.material_checklist.filter((i: { required: boolean; uploaded: boolean }) => i.required && !i.uploaded).length > 0 && (
                    <span style={{ color: '#ff4d4f' }}>（{p.material_checklist.filter((i: { required: boolean; uploaded: boolean }) => i.required && !i.uploaded).length} 项必传未完成）</span>
                  )}
                </p>
              )}
              {p.company_info && typeof p.company_info === 'object' && String((p.company_info as Record<string, unknown>).legal_representative || '') && (
                <p style={{ color: '#888', fontSize: 12 }}>
                  法人：{String((p.company_info as Record<string, unknown>).legal_representative || '')}
                  {String((p.company_info as Record<string, unknown>).registered_capital || '') && (
                    <> | 注册资本：{String((p.company_info as Record<string, unknown>).registered_capital || '')}</>
                  )}
                </p>
              )}
            </Card>
          ))}
        </div>
      )}

      <Modal
        title="新建申报项目"
        open={open}
        onOk={handleCreate}
        onCancel={handleClose}
        okText="创建"
        confirmLoading={creating}
        width={640}
      >
        <Form form={form} layout="vertical">
          <Form.Item name="name" label="项目名称" rules={[{ required: true, message: '请输入项目名称' }]}>
            <Input placeholder="例如：XX公司2025年高企申报" />
          </Form.Item>
          <Form.Item name="project_type" label="申报类型" rules={[{ required: true, message: '请选择申报类型' }]}>
            <Select options={[
              { value: 'gaoxin', label: '国家高新技术企业' },
              { value: 'xiaojuren', label: '专精特新小巨人' },
            ]} />
          </Form.Item>
          <Form.Item name="company_name" label="企业名称">
            <Input.Search
              placeholder="输入企业全称后点击搜索自动填充信息"
              enterButton={searching ? <LoadingOutlined /> : <SearchOutlined />}
              onSearch={handleSearchCompany}
              loading={searching}
            />
          </Form.Item>
        </Form>

        {searching && (
          <div style={{ textAlign: 'center', padding: 20 }}>
            <Spin tip="正在搜索企业信息..." />
          </div>
        )}

        {searchError && (
          <Alert type="warning" message={searchError} showIcon style={{ marginBottom: 16 }} />
        )}

        {companyInfo?.found && (
          <Card title={`企业信息 (来源: ${companyInfo.source || '搜索结果'})`} size="small" style={{ marginTop: 8 }}>
            <Descriptions column={2} size="small" bordered>
              {companyInfo.legal_representative && (
                <Descriptions.Item label="法定代表人">{companyInfo.legal_representative}</Descriptions.Item>
              )}
              {companyInfo.registered_capital && (
                <Descriptions.Item label="注册资本">{companyInfo.registered_capital}</Descriptions.Item>
              )}
              {companyInfo.established_date && (
                <Descriptions.Item label="成立日期">{companyInfo.established_date}</Descriptions.Item>
              )}
              {companyInfo.business_status && (
                <Descriptions.Item label="经营状态">{companyInfo.business_status}</Descriptions.Item>
              )}
              {companyInfo.unified_code && (
                <Descriptions.Item label="统一社会信用代码">{companyInfo.unified_code}</Descriptions.Item>
              )}
              {companyInfo.company_type && (
                <Descriptions.Item label="企业类型">{companyInfo.company_type}</Descriptions.Item>
              )}
              {companyInfo.industry && (
                <Descriptions.Item label="所属行业">{companyInfo.industry}</Descriptions.Item>
              )}
              {companyInfo.address && (
                <Descriptions.Item label="注册地址" span={2}>{companyInfo.address}</Descriptions.Item>
              )}
              {companyInfo.business_scope && (
                <Descriptions.Item label="经营范围" span={2}>{companyInfo.business_scope}</Descriptions.Item>
              )}
            </Descriptions>
          </Card>
        )}
      </Modal>
    </div>
  );
}
