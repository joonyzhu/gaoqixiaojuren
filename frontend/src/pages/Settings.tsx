import { useState, useEffect } from 'react';
import {
  Typography, Card, Form, Input, Button, Tabs, List, Tag, message,
  Spin, Alert, Modal, Popconfirm, Empty, Select, Upload,
} from 'antd';
import {
  CheckCircleOutlined, CloseCircleOutlined, ApiOutlined,
  ReloadOutlined, PlayCircleOutlined, PlusOutlined,
  DeleteOutlined, LinkOutlined, FileTextOutlined,
  DownloadOutlined, StarOutlined,
} from '@ant-design/icons';
import api from '../services/api';

interface ModelItem {
  id: string;
  name: string;
  provider: string;
  available: boolean;
  configured: boolean;
  is_custom?: boolean;
  base_url?: string;
}

interface CustomModelItem {
  id: string;
  name: string;
  base_url: string;
  api_key_set: boolean;
  provider_label: string;
}

interface TemplateItem {
  id: string;
  name: string;
  project_type: string;
  original_filename: string;
  is_builtin: boolean;
  is_active: boolean;
  created_at: string;
}

const providerNames: Record<string, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  gemini: 'Google',
  qwen: '阿里通义千问',
  qianfan: '百度文心一言',
  deepseek: 'DeepSeek',
  zhipu: '智谱 GLM',
  moonshot: 'Kimi 月之暗面',
  tavily: 'Tavily 联网搜索',
};

const providerFields: Record<string, { label: string; keys: string[] }[]> = {
  anthropic: [{ label: 'Anthropic API Key', keys: ['anthropic_api_key'] }],
  openai: [{ label: 'OpenAI API Key', keys: ['openai_api_key'] }],
  gemini: [{ label: 'Google API Key', keys: ['google_api_key'] }],
  qwen: [{ label: 'DashScope API Key', keys: ['dashscope_api_key'] }],
  qianfan: [
    { label: '百度 Access Key', keys: ['qianfan_access_key'] },
    { label: '百度 Secret Key', keys: ['qianfan_secret_key'] },
  ],
  deepseek: [{ label: 'DeepSeek API Key', keys: ['deepseek_api_key'] }],
  zhipu: [{ label: '智谱 API Key', keys: ['zhipu_api_key'] }],
  moonshot: [{ label: 'Kimi API Key', keys: ['moonshot_api_key'] }],
  tavily: [{ label: 'Tavily Search API Key (联网搜索)', keys: ['tavily_api_key'] }],
};

export default function Settings() {
  const [form] = Form.useForm();
  const [customForm] = Form.useForm();
  const [models, setModels] = useState<ModelItem[]>([]);
  const [customModels, setCustomModels] = useState<CustomModelItem[]>([]);
  const [loadingModels, setLoadingModels] = useState(false);
  const [testing, setTesting] = useState<string | null>(null);
  const [testResults, setTestResults] = useState<Record<string, boolean>>({});
  const [customModalOpen, setCustomModalOpen] = useState(false);
  const [saving, setSaving] = useState(false);
  const [templates, setTemplates] = useState<TemplateItem[]>([]);
  const [loadingTemplates, setLoadingTemplates] = useState(false);
  const [tplForm] = Form.useForm();
  const [tplModalOpen, setTplModalOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [tplFile, setTplFile] = useState<File | null>(null);

  const loadModels = async () => {
    setLoadingModels(true);
    try {
      const resp = await api.get('/llm/models');
      setModels(resp.data);
    } catch {
      // Backend may not be running
    } finally {
      setLoadingModels(false);
    }
  };

  const loadCustomModels = async () => {
    try {
      const resp = await api.get('/llm/custom-models');
      setCustomModels(resp.data);
    } catch {
      // Backend may not be running
    }
  };

  const loadTemplates = async () => {
    setLoadingTemplates(true);
    try {
      const resp = await api.get('/templates');
      setTemplates(resp.data || []);
    } catch {
      // Backend may not be running
    } finally {
      setLoadingTemplates(false);
    }
  };

  useEffect(() => {
    loadModels();
    loadCustomModels();
    loadTemplates();
  }, []);

  const handleSave = async () => {
    try {
      const values = await form.validateFields();
      Object.entries(values).forEach(([key, value]) => {
        if (value) localStorage.setItem(key, value as string);
      });
      message.success('配置已保存，重新加载模型列表...');
      await loadModels();
    } catch {
      // validation failed
    }
  };

  const handleTest = async (modelId: string) => {
    setTesting(modelId);
    try {
      const resp = await api.post('/llm/test', { model_id: modelId });
      setTestResults({ ...testResults, [modelId]: resp.data.connected });
      if (resp.data.connected) {
        message.success(`${modelId} 连接成功`);
      } else {
        message.error(`${modelId} 连接失败`);
      }
    } catch {
      setTestResults({ ...testResults, [modelId]: false });
    } finally {
      setTesting(null);
    }
  };

  const handleAddCustomModel = async () => {
    try {
      const values = await customForm.validateFields();
      setSaving(true);
      await api.post('/llm/custom-models', values);
      message.success(`自定义模型 ${values.id} 已添加`);
      setCustomModalOpen(false);
      customForm.resetFields();
      await loadCustomModels();
      await loadModels();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      message.error('添加失败，请检查参数');
    } finally {
      setSaving(false);
    }
  };

  const handleDeleteCustomModel = async (modelId: string) => {
    try {
      await api.delete(`/llm/custom-models/${modelId}`);
      message.success(`${modelId} 已删除`);
      await loadCustomModels();
      await loadModels();
    } catch {
      message.error('删除失败');
    }
  };

  const handleUploadTemplate = async () => {
    try {
      const values = await tplForm.validateFields();
      if (!tplFile) {
        message.error('请选择文件');
        return;
      }
      setUploading(true);
      const formData = new FormData();
      formData.append('file', tplFile);
      formData.append('name', values.name || tplFile.name);
      formData.append('project_type', values.project_type || 'both');
      formData.append('set_active', values.set_active ? 'true' : 'false');
      await api.post('/templates/upload', formData, {
        headers: { 'Content-Type': 'multipart/form-data' },
      });
      message.success('模板上传成功');
      setTplModalOpen(false);
      tplForm.resetFields();
      setTplFile(null);
      await loadTemplates();
    } catch (err: unknown) {
      if (err && typeof err === 'object' && 'errorFields' in err) return;
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(detail || '上传失败');
    } finally {
      setUploading(false);
    }
  };

  const handleActivateTemplate = async (templateId: string) => {
    try {
      await api.put(`/templates/${templateId}/activate`);
      message.success('已设为默认模板');
      await loadTemplates();
    } catch {
      message.error('操作失败');
    }
  };

  const handleDeleteTemplate = async (templateId: string) => {
    try {
      await api.delete(`/templates/${templateId}`);
      message.success('模板已删除');
      await loadTemplates();
    } catch {
      message.error('删除失败');
    }
  };

  const handleDownloadTemplate = (templateId: string) => {
    window.open(`${api.defaults.baseURL}/templates/${templateId}/download`, '_blank');
  };

  const modelsByProvider: Record<string, ModelItem[]> = {};
  models.forEach((m) => {
    if (!modelsByProvider[m.provider]) modelsByProvider[m.provider] = [];
    modelsByProvider[m.provider].push(m);
  });

  const customProviderModels = Object.entries(modelsByProvider)
    .filter(([k]) => k.startsWith('custom_'));

  return (
    <div style={{ maxWidth: 800 }}>
      <Typography.Title level={3}>系统设置</Typography.Title>

      <Tabs items={[
        {
          key: 'api',
          label: <span><ApiOutlined /> API 密钥配置</span>,
          children: (
            <Card title="大模型 API 密钥">
              <Alert
                message="配置至少一个模型的 API Key 即可开始使用。密钥仅保存在本地浏览器中。"
                type="info"
                showIcon
                style={{ marginBottom: 16 }}
              />
              <Form form={form} layout="vertical">
                {Object.entries(providerFields).map(([provider, fields]) => (
                  <Card
                    key={provider}
                    size="small"
                    title={providerNames[provider] || provider}
                    style={{ marginBottom: 12 }}
                  >
                    {fields.map((field) => (
                      <Form.Item key={field.keys[0]} name={field.keys[0]} label={field.label}>
                        <Input.Password placeholder="输入 API Key..." />
                      </Form.Item>
                    ))}
                  </Card>
                ))}
                <Button type="primary" onClick={handleSave} icon={<ApiOutlined />}>
                  保存所有 API 配置
                </Button>
              </Form>
            </Card>
          ),
        },
        {
          key: 'models',
          label: '模型管理',
          children: (
            <Card
              title="已接入模型"
              extra={
                <Button onClick={loadModels} loading={loadingModels} icon={<ReloadOutlined />}>
                  刷新
                </Button>
              }
            >
              {loadingModels ? (
                <Spin />
              ) : (
                Object.entries(modelsByProvider)
                  .filter(([k]) => !k.startsWith('custom_'))
                  .map(([provider, providerModels]) => (
                  <Card
                    key={provider}
                    size="small"
                    title={providerNames[provider] || provider}
                    style={{ marginBottom: 12 }}
                  >
                    <List
                      dataSource={providerModels}
                      renderItem={(m) => (
                        <List.Item
                          actions={[
                            m.configured ? (
                              <Tag icon={<CheckCircleOutlined />} color="success">已配置</Tag>
                            ) : (
                              <Tag icon={<CloseCircleOutlined />} color="default">未配置</Tag>
                            ),
                            testResults[m.id] ? (
                              <Tag color="success">连接正常</Tag>
                            ) : testResults[m.id] === false ? (
                              <Tag color="error">连接失败</Tag>
                            ) : null,
                            <Button
                              size="small"
                              onClick={() => handleTest(m.id)}
                              loading={testing === m.id}
                              disabled={!m.configured}
                              icon={<PlayCircleOutlined />}
                            >
                              测试
                            </Button>,
                          ]}
                        >
                          <List.Item.Meta title={m.name} description={`ID: ${m.id}`} />
                        </List.Item>
                      )}
                    />
                  </Card>
                ))
              )}
            </Card>
          ),
        },
        {
          key: 'custom',
          label: <span><LinkOutlined /> 自定义模型</span>,
          children: (
            <div>
              <Card
                title="自定义 OpenAI 兼容模型"
                extra={
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => setCustomModalOpen(true)}>
                    添加模型
                  </Button>
                }
              >
                <Alert
                  message="兼容任何 OpenAI API 格式的服务（如 ollama、vLLM、SiliconFlow、Groq 等），只需提供 Base URL、API Key 和模型 ID。"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                {customModels.length === 0 && customProviderModels.length === 0 ? (
                  <Empty description="暂无自定义模型，点击上方按钮添加" />
                ) : (
                  <>
                    {customProviderModels.map(([provider, providerModels]) => (
                      <Card key={provider} size="small" title="自定义接入" style={{ marginBottom: 12 }}>
                        <List
                          dataSource={providerModels}
                          renderItem={(m) => (
                            <List.Item
                              actions={[
                                <Tag icon={<CheckCircleOutlined />} color="success">已配置</Tag>,
                                testResults[m.id] ? (
                                  <Tag color="success">连接正常</Tag>
                                ) : testResults[m.id] === false ? (
                                  <Tag color="error">连接失败</Tag>
                                ) : null,
                                <Button
                                  size="small"
                                  onClick={() => handleTest(m.id)}
                                  loading={testing === m.id}
                                  icon={<PlayCircleOutlined />}
                                >
                                  测试
                                </Button>,
                                <Popconfirm
                                  title="确定删除此模型？"
                                  onConfirm={() => handleDeleteCustomModel(m.id)}
                                >
                                  <Button size="small" danger icon={<DeleteOutlined />} />
                                </Popconfirm>,
                              ]}
                            >
                              <List.Item.Meta
                                title={m.name}
                                description={
                                  <span>
                                    ID: {m.id}
                                    {m.base_url && <span> | {m.base_url}</span>}
                                  </span>
                                }
                              />
                            </List.Item>
                          )}
                        />
                      </Card>
                    ))}
                  </>
                )}
              </Card>

              <Modal
                title="添加自定义模型"
                open={customModalOpen}
                onOk={handleAddCustomModel}
                onCancel={() => { setCustomModalOpen(false); customForm.resetFields(); }}
                confirmLoading={saving}
                okText="添加"
              >
                <Form form={customForm} layout="vertical">
                  <Form.Item
                    name="id"
                    label="模型 ID"
                    rules={[{ required: true, message: '请输入模型 ID' }]}
                    extra="API 调用时使用的 model 参数值，如 gpt-4、llama3、qwen2.5"
                  >
                    <Input placeholder="例如: gpt-4o, deepseek-chat, qwen2.5-72b" />
                  </Form.Item>
                  <Form.Item
                    name="name"
                    label="显示名称"
                    rules={[{ required: true, message: '请输入显示名称' }]}
                  >
                    <Input placeholder="例如: 我的本地 Llama3" />
                  </Form.Item>
                  <Form.Item
                    name="base_url"
                    label="API Base URL"
                    rules={[{ required: true, message: '请输入 API 地址' }]}
                    extra="OpenAI 兼容的 API 端点地址"
                  >
                    <Input placeholder="例如: http://localhost:11434/v1 或 https://api.siliconflow.cn/v1" />
                  </Form.Item>
                  <Form.Item name="api_key" label="API Key (可选)">
                    <Input.Password placeholder="如服务不需要鉴权可留空" />
                  </Form.Item>
                </Form>
              </Modal>
            </div>
          ),
        },
        {
          key: 'templates',
          label: <span><FileTextOutlined /> 模板管理</span>,
          children: (
            <div>
              <Card
                title="导出模板 (.docx)"
                extra={
                  <Button type="primary" icon={<PlusOutlined />} onClick={() => setTplModalOpen(true)}>
                    上传模板
                  </Button>
                }
              >
                <Alert
                  message="上传 .docx 模板文件。在模板中使用 {company_name}、{basic} 等占位符标记 AI 内容的插入位置。导出时系统会自动将占位符替换为 AI 生成的内容。"
                  type="info"
                  showIcon
                  style={{ marginBottom: 16 }}
                />

                {loadingTemplates ? (
                  <Spin />
                ) : templates.length === 0 ? (
                  <Empty description="暂无模板，点击上方按钮上传" />
                ) : (
                  <List
                    dataSource={templates}
                    renderItem={(tpl) => (
                      <List.Item
                        actions={[
                          tpl.is_active && <Tag color="gold" icon={<StarOutlined />}>当前默认</Tag>,
                          !tpl.is_active && (
                            <Button size="small" onClick={() => handleActivateTemplate(tpl.id)}>
                              设为默认
                            </Button>
                          ),
                          <Button
                            size="small"
                            icon={<DownloadOutlined />}
                            onClick={() => handleDownloadTemplate(tpl.id)}
                          >
                            下载
                          </Button>,
                          !tpl.is_builtin && (
                            <Popconfirm
                              title="确定删除此模板？"
                              onConfirm={() => handleDeleteTemplate(tpl.id)}
                            >
                              <Button size="small" danger icon={<DeleteOutlined />} />
                            </Popconfirm>
                          ),
                        ]}
                      >
                        <List.Item.Meta
                          title={
                            <span>
                              {tpl.name}
                              {tpl.is_builtin && <Tag color="blue" style={{ marginLeft: 8 }}>内置</Tag>}
                            </span>
                          }
                          description={
                            <span>
                              适用类型: {tpl.project_type === 'both' ? '通用' : tpl.project_type === 'gaoxin' ? '高企' : '小巨人'}
                              {' | '}
                              文件: {tpl.original_filename}
                            </span>
                          }
                        />
                      </List.Item>
                    )}
                  />
                )}
              </Card>

              <Card title="占位符说明" size="small" style={{ marginTop: 16 }}>
                <p>通用占位符: <Tag>{'{company_name}'}</Tag> <Tag>{'{project_name}'}</Tag> <Tag>{'{date}'}</Tag></p>
                <p>高企模板: <Tag>{'{basic}'}</Tag> <Tag>{'{rd}'}</Tag> <Tag>{'{ip}'}</Tag> <Tag>{'{product}'}</Tag> <Tag>{'{staff}'}</Tag> <Tag>{'{innovation}'}</Tag> <Tag>{'{appendix}'}</Tag></p>
                <p>小巨人模板: <Tag>{'{basic}'}</Tag> <Tag>{'{specialization}'}</Tag> <Tag>{'{refinement}'}</Tag> <Tag>{'{characteristic}'}</Tag> <Tag>{'{innovation}'}</Tag> <Tag>{'{chain}'}</Tag> <Tag>{'{management}'}</Tag> <Tag>{'{appendix}'}</Tag></p>
                <p style={{ color: '#888' }}>模板中放入占位符即会在导出时替换为 AI 生成内容。每个章节占位符会替换为对应 AI 生成的完整文本。</p>
              </Card>

              <Modal
                title="上传导出模板"
                open={tplModalOpen}
                onOk={handleUploadTemplate}
                onCancel={() => { setTplModalOpen(false); tplForm.resetFields(); setTplFile(null); }}
                confirmLoading={uploading}
                okText="上传"
              >
                <Form form={tplForm} layout="vertical">
                  <Form.Item
                    name="file"
                    label="模板文件 (.docx)"
                    rules={[{ required: true, message: '请选择文件' }]}
                  >
                    <Upload
                      beforeUpload={(file) => { setTplFile(file); return false; }}
                      maxCount={1}
                      accept=".docx,.doc"
                      onRemove={() => setTplFile(null)}
                    >
                      <Button icon={<PlusOutlined />}>选择文件</Button>
                    </Upload>
                  </Form.Item>
                  <Form.Item name="name" label="模板名称（可选）">
                    <Input placeholder="留空则使用文件名" />
                  </Form.Item>
                  <Form.Item
                    name="project_type"
                    label="适用申报类型"
                    initialValue="both"
                  >
                    <Select options={[
                      { value: 'gaoxin', label: '国家高新技术企业' },
                      { value: 'xiaojuren', label: '专精特新小巨人' },
                      { value: 'both', label: '通用（两种都适用）' },
                    ]} />
                  </Form.Item>
                  <Form.Item name="set_active" label="设为默认模板" initialValue={false}>
                    <Select options={[
                      { value: true, label: '是' },
                      { value: false, label: '否' },
                    ]} />
                  </Form.Item>
                </Form>
              </Modal>
            </div>
          ),
        },
      ]} />
    </div>
  );
}
