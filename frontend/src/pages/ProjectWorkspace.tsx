import { useState, useEffect, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Typography, Card, Button, Layout, Menu, Spin, Space, Select,
  message, Tag, Empty, Input, Drawer, Breadcrumb, Result,
  Tabs, Tooltip, Modal, Steps,
} from 'antd';
import {
  PlayCircleOutlined, ExportOutlined, AuditOutlined,
  FileTextOutlined,
  HolderOutlined, LeftOutlined, RightOutlined, HomeOutlined,
  SaveOutlined, LoadingOutlined, EyeOutlined,
  CommentOutlined, HistoryOutlined,
} from '@ant-design/icons';
import api from '../services/api';
import MaterialChecklist from '../components/MaterialChecklist';
import DocumentPreview from '../components/DocumentPreview';
import SectionComments from '../components/SectionComments';
import RevisionHistory from '../components/RevisionHistory';

const { Sider, Content } = Layout;

interface Section {
  id: string;
  title: string;
  order: number;
}

interface ProjectData {
  id: string;
  name: string;
  project_type: string;
  status: string;
  phase: string;
  company_name: string;
  company_info: Record<string, unknown>;
  financial_data: Record<string, unknown>;
  ip_data: Record<string, unknown>;
  rd_data: Record<string, unknown>;
  content: Record<string, { title: string; content: string; model?: string }>;
  material_checklist: Array<{
    id: string;
    category: string;
    item: string;
    required: boolean;
    description: string;
    uploaded: boolean;
    doc_ids: string[];
  }>;
  checklist_stats?: {
    total_items: number;
    required_items: number;
    completed_items: number;
    required_completed: number;
    completion_pct: number;
    all_required_done: boolean;
  };
  review_score: number;
  review_summary: string;
}

function useSections(projectType: string | undefined) {
  const [sections, setSections] = useState<Section[]>([]);
  useEffect(() => {
    if (projectType) {
      api.get(`/engine/sections/${projectType}`).then((r) => setSections(r.data)).catch(() => {});
    }
  }, [projectType]);
  return sections;
}

export default function ProjectWorkspace() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [project, setProject] = useState<ProjectData | null>(null);
  const [loading, setLoading] = useState(true);
  const [notFound, setNotFound] = useState(false);
  const sections = useSections(project?.project_type);

  const [selectedSection, setSelectedSection] = useState<string>('');
  const [contentMap, setContentMap] = useState<Record<string, { title: string; content: string; model?: string }>>({});
  const [selectedModel, setSelectedModel] = useState('');
  const [generating, setGenerating] = useState(false);
  const [streamingContent, setStreamingContent] = useState('');
  const [reviewResult, setReviewResult] = useState('');
  const [reviewing, setReviewing] = useState(false);
  const [reviewDrawer, setReviewDrawer] = useState(false);
  const [collapsed, setCollapsed] = useState(false);
  const [saving, setSaving] = useState(false);
  const [models, setModels] = useState<{ id: string; name: string; configured: boolean }[]>([]);
  const [feedback, setFeedback] = useState('');
  const [previewOpen, setPreviewOpen] = useState(false);
  const [bottomTab, setBottomTab] = useState('comments');

  const contentRef = useRef<HTMLDivElement>(null);
  const contentMapRef = useRef(contentMap);
  contentMapRef.current = contentMap;  // Always keep ref in sync with state

  // Load project
  useEffect(() => {
    if (!id) { setLoading(false); setNotFound(true); return; }
    setLoading(true);
    api.get(`/projects/${id}`)
      .then((resp) => {
        const p = resp.data;
        setProject(p);
        setContentMap(p.content || {});
        setNotFound(false);
      })
      .catch(() => setNotFound(true))
      .finally(() => setLoading(false));
  }, [id]);

  // Load models
  useEffect(() => {
    api.get('/llm/models').then((r) => {
      const all = r.data || [];
      setModels(all);
      const configured = all.filter((m: { configured: boolean }) => m.configured);
      if (configured.length > 0) setSelectedModel(configured[0].id);
    }).catch(() => {});
  }, []);

  // Auto-select first section
  useEffect(() => {
    if (sections.length > 0 && !selectedSection) {
      setSelectedSection(sections[0].id);
    }
  }, [sections, selectedSection]);

  // Auto-scroll streaming
  useEffect(() => {
    if (contentRef.current) {
      contentRef.current.scrollTop = contentRef.current.scrollHeight;
    }
  }, [streamingContent]);

  const refreshProject = useCallback(async () => {
    if (!id) return;
    try {
      const resp = await api.get(`/projects/${id}`);
      setProject(resp.data);
      setContentMap(resp.data.content || {});
    } catch { /* ignore */ }
  }, [id]);

  const handleSave = useCallback(async () => {
    if (!id) return;
    setSaving(true);
    try {
      await api.patch(`/projects/${id}`, {
        content: JSON.stringify(contentMapRef.current),
      });
      message.success('已保存');
    } catch {
      message.error('保存失败');
    } finally {
      setSaving(false);
    }
  }, [id]);

  const getWebSearchKey = () => localStorage.getItem('tavily_api_key') || '';

  const handleGenerate = useCallback(async () => {
    if (!selectedSection || !selectedModel || !id) {
      message.warning('请先选择章节和模型');
      return;
    }

    setGenerating(true);
    setStreamingContent('');

    try {
      const resp = await fetch('http://localhost:8100/api/engine/compose-section-stream', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          project_id: id,
          section_id: selectedSection,
          model_id: selectedModel,
          web_search_key: getWebSearchKey(),
          feedback: feedback,
        }),
      });

      if (!resp.ok) {
        const err = await resp.json();
        message.error(err.detail || '请求失败');
        setGenerating(false);
        return;
      }

      const reader = resp.body?.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let accumulated = '';

      while (reader) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              if (data.status === 'generating') {
                accumulated += data.content;
                setStreamingContent(accumulated);
              } else if (data.status === 'done') {
                const fullContent = data.content || accumulated;
                const newContent = {
                  ...contentMapRef.current,
                  [data.section_id]: { title: data.title, content: fullContent },
                };
                setContentMap(newContent);
                setStreamingContent('');
                setFeedback('');
                message.success(`${data.title} 生成完成`);
                api.patch(`/projects/${id}`, {
                  content: JSON.stringify(newContent),
                  phase: 'writing',
                }).catch(() => {});
                refreshProject();
              } else if (data.status === 'error') {
                message.error(data.error || '生成失败');
                setStreamingContent('');
              }
            } catch { /* parse error */ }
          }
        }
      }
    } catch {
      message.error('连接失败，请确保后端已启动');
    } finally {
      setGenerating(false);
    }
  }, [selectedSection, selectedModel, id, feedback, refreshProject]);

  const handleReview = useCallback(async () => {
    if (!id || !selectedModel) return;
    setReviewing(true);
    setReviewResult('');
    setReviewDrawer(true);
    try {
      const resp = await api.post('/engine/review', {
        project_id: id,
        model_id: selectedModel,
        web_search_key: getWebSearchKey(),
      });
      setReviewResult(resp.data.summary || '');
      refreshProject();
    } catch {
      message.error('审查失败');
    } finally {
      setReviewing(false);
    }
  }, [id, selectedModel, refreshProject]);

  const handleExport = useCallback(async () => {
    if (!id) return;
    try {
      const resp = await api.post('/engine/export', { project_id: id }, { responseType: 'blob' });
      const url = window.URL.createObjectURL(new Blob([resp.data]));
      const a = document.createElement('a');
      a.href = url;
      a.download = `${project?.company_name || '申报书'}_${project?.project_type === 'gaoxin' ? '高企' : '小巨人'}.docx`;
      a.click();
      window.URL.revokeObjectURL(url);
      message.success('导出成功');
    } catch (err: unknown) {
      const detail = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      message.error(detail || '导出失败');
    }
  }, [id, project]);

  const handleStartWriting = useCallback(async () => {
    if (!id) return;
    try {
      await api.patch(`/projects/${id}`, { phase: 'writing' });
      await refreshProject();
    } catch {
      message.error('状态更新失败');
    }
  }, [id, refreshProject]);

  const generatedCount = Object.keys(contentMap).length;
  const totalCount = sections.length;

  if (loading) {
    return <div style={{ textAlign: 'center', padding: 100 }}><Spin size="large" /></div>;
  }

  if (notFound || !project) {
    return (
      <Result
        status="404"
        title="项目未找到"
        subTitle="该项目可能已被删除或不存在"
        extra={<Button type="primary" onClick={() => navigate('/')} icon={<HomeOutlined />}>返回首页</Button>}
      />
    );
  }

  const phaseStep = project.phase === 'materials' ? 0
    : project.phase === 'writing' ? 1
    : project.phase === 'review' ? 2
    : 3;

  // ── MATERIALS PHASE ──
  if (project.phase === 'materials') {
    const checklistData = project.material_checklist || [];
    const stats = project.checklist_stats || {
      total_items: checklistData.length,
      required_items: checklistData.filter((i) => i.required).length,
      completed_items: checklistData.filter((i) => i.uploaded).length,
      required_completed: checklistData.filter((i) => i.required && i.uploaded).length,
      completion_pct: checklistData.length ? Math.round(checklistData.filter((i) => i.uploaded).length / checklistData.length * 100 * 10) / 10 : 0,
      all_required_done: checklistData.filter((i) => i.required).every((i) => i.uploaded),
    };

    return (
      <div>
        <Breadcrumb style={{ marginBottom: 12 }} items={[
          { title: <a onClick={() => navigate('/')}><HomeOutlined /> 项目总览</a> },
          { title: project.name },
        ]} />
        <Steps
          current={0}
          size="small"
          style={{ marginBottom: 24 }}
          items={[
            { title: '材料收集' },
            { title: 'AI 撰写' },
            { title: '质量审查' },
            { title: '导出' },
          ]}
        />
        <MaterialChecklist
          projectId={project.id}
          checklist={checklistData}
          stats={stats}
          onStartWriting={handleStartWriting}
          onRefresh={refreshProject}
        />
      </div>
    );
  }

  // ── WRITING / REVIEW PHASE ──
  const menuItems = sections.map((s) => ({
    key: s.id,
    icon: <HolderOutlined />,
    label: collapsed ? undefined : (
      <span>
        {s.title}
        {contentMap[s.id] && (
          <Tag color="success" style={{ marginLeft: 8, fontSize: 10 }}>✓</Tag>
        )}
        {generating && selectedSection === s.id && (
          <LoadingOutlined style={{ marginLeft: 8 }} />
        )}
      </span>
    ),
  }));

  const canExport = project.phase === 'review' || project.phase === 'done';

  return (
    <div>
      <Breadcrumb style={{ marginBottom: 12 }} items={[
        { title: <a onClick={() => navigate('/')}><HomeOutlined /> 项目总览</a> },
        { title: project.name },
      ]} />

      <Steps
        current={phaseStep}
        size="small"
        style={{ marginBottom: 16 }}
        items={[
          { title: '材料收集' },
          { title: 'AI 撰写' },
          { title: '质量审查' },
          { title: '导出' },
        ]}
      />

      <Layout hasSider style={{ background: '#f5f5f5', minHeight: 'calc(100vh - 200px)' }}>
        <Sider
          width={collapsed ? 60 : 260}
          style={{ background: '#fff', padding: '12px 0', transition: 'width 0.2s' }}
        >
          <div style={{ padding: '0 16px', marginBottom: 12 }}>
            <Button
              type="text"
              icon={collapsed ? <RightOutlined /> : <LeftOutlined />}
              onClick={() => setCollapsed(!collapsed)}
              style={{ marginBottom: 8 }}
            />
            {!collapsed && (
              <>
                <Typography.Text strong style={{ fontSize: 13 }}>
                  章节 ({generatedCount}/{totalCount})
                </Typography.Text>
                <div style={{ marginTop: 8 }}>
                  <Select
                    value={selectedModel || undefined}
                    onChange={setSelectedModel}
                    options={models.map((m) => ({
                      value: m.id,
                      label: `${m.name}${!m.configured ? ' (未配置)' : ''}`,
                      disabled: !m.configured,
                    }))}
                    style={{ width: '100%' }}
                    size="small"
                    placeholder="选择模型"
                    notFoundContent="请先配置 API Key"
                  />
                </div>
                <div style={{ marginTop: 8 }}>
                  <Typography.Text type="secondary" style={{ fontSize: 11 }}>
                    阶段：{project.phase === 'writing' ? 'AI 撰写' : project.phase === 'review' ? '质量审查' : project.phase}
                  </Typography.Text>
                </div>
              </>
            )}
          </div>
          <Menu
            mode="inline"
            selectedKeys={[selectedSection]}
            items={menuItems}
            onClick={({ key }) => { setSelectedSection(key); setStreamingContent(''); }}
            style={{ borderRight: 0 }}
          />
        </Sider>

        <Content style={{ padding: 16, overflow: 'auto' }}>
          {!selectedSection ? (
            <Card style={{ textAlign: 'center', padding: 80 }}>
              <FileTextOutlined style={{ fontSize: 56, color: '#d9d9d9' }} />
              <Typography.Title level={4} style={{ color: '#999', marginTop: 16 }}>
                选择一个章节开始撰写
              </Typography.Title>
            </Card>
          ) : (
            <div>
              <Card size="small" style={{ marginBottom: 12 }}>
                <Space style={{ width: '100%', justifyContent: 'space-between' }} wrap>
                  <Space>
                    <Typography.Text strong style={{ fontSize: 15 }}>
                      {sections.find((s) => s.id === selectedSection)?.title}
                    </Typography.Text>
                    {contentMap[selectedSection] && (
                      <Tag color="success">
                        {contentMap[selectedSection]?.content?.length || 0} 字
                      </Tag>
                    )}
                  </Space>
                  <Space>
                    <Button
                      icon={<SaveOutlined />}
                      onClick={handleSave}
                      loading={saving}
                    >
                      保存
                    </Button>
                    <Button
                      icon={<EyeOutlined />}
                      onClick={() => setPreviewOpen(true)}
                      disabled={generatedCount === 0}
                    >
                      预览
                    </Button>
                    <Button
                      type="primary"
                      icon={generating ? <LoadingOutlined /> : <PlayCircleOutlined />}
                      onClick={handleGenerate}
                      loading={generating}
                      disabled={!selectedModel}
                    >
                      {generating ? '生成中...' : 'AI 生成'}
                    </Button>
                    <Button
                      icon={<AuditOutlined />}
                      onClick={handleReview}
                      loading={reviewing}
                      disabled={generatedCount === 0}
                    >
                      审查
                    </Button>
                    <Tooltip title={canExport ? '' : '请先完成质量审查'}>
                      <Button
                        icon={<ExportOutlined />}
                        onClick={handleExport}
                        disabled={!canExport || generatedCount === 0}
                      >
                        导出
                      </Button>
                    </Tooltip>
                  </Space>
                </Space>

                {/* Feedback input for regeneration */}
                <div style={{ marginTop: 8 }}>
                  <Input.TextArea
                    placeholder="修改意见（可选）：描述你希望对本章节做的修改，重新生成时将带入此意见..."
                    value={feedback}
                    onChange={(e) => setFeedback(e.target.value)}
                    rows={2}
                    style={{ fontSize: 12 }}
                  />
                </div>
              </Card>

              <Card bodyStyle={{ padding: 0 }}>
                <div
                  ref={contentRef}
                  style={{
                    maxHeight: 'calc(100vh - 500px)',
                    overflow: 'auto',
                    padding: 16,
                    background: '#fff',
                    border: '1px solid #f0f0f0',
                    borderRadius: 8,
                    fontFamily: '"PingFang SC", "Microsoft YaHei", sans-serif',
                    fontSize: 14,
                    lineHeight: 2,
                    whiteSpace: 'pre-wrap',
                    minHeight: 200,
                  }}
                >
                  {contentMap[selectedSection]?.content && !streamingContent && (
                    <Input.TextArea
                      value={contentMap[selectedSection].content}
                      onChange={(e) => setContentMap((prev) => ({
                        ...prev,
                        [selectedSection]: {
                          ...prev[selectedSection],
                          content: e.target.value,
                        },
                      }))}
                      autoSize={{ minRows: 8 }}
                      style={{
                        border: 'none',
                        resize: 'none',
                        fontFamily: 'inherit',
                        fontSize: 'inherit',
                        lineHeight: 'inherit',
                        background: 'transparent',
                      }}
                    />
                  )}

                  {streamingContent && (
                    <div style={{ color: '#333' }}>
                      {streamingContent}
                      <span style={{
                        display: 'inline-block', width: 2, height: 18,
                        background: '#1890ff', marginLeft: 2,
                        verticalAlign: 'text-bottom',
                        animation: 'blink 1s infinite',
                      }} />
                    </div>
                  )}

                  {!contentMap[selectedSection] && !streamingContent && (
                    <Empty
                      description="点击「AI 生成」按钮开始撰写此章节"
                      style={{ paddingTop: 40 }}
                    />
                  )}
                </div>
              </Card>

              {/* Comments and Revision History tabs below content */}
              {contentMap[selectedSection] && (
                <Card size="small" style={{ marginTop: 12 }}>
                  <Tabs
                    activeKey={bottomTab}
                    onChange={setBottomTab}
                    items={[
                      {
                        key: 'comments',
                        label: <span><CommentOutlined /> 修改意见</span>,
                        children: <SectionComments projectId={project.id} sectionId={selectedSection} />,
                      },
                      {
                        key: 'history',
                        label: <span><HistoryOutlined /> 修订历史</span>,
                        children: (
                          <RevisionHistory
                            projectId={project.id}
                            sectionId={selectedSection}
                            onRestore={(content) => {
                              setContentMap((prev) => ({
                                ...prev,
                                [selectedSection]: {
                                  ...prev[selectedSection],
                                  content,
                                },
                              }));
                            }}
                          />
                        ),
                      },
                    ]}
                  />
                </Card>
              )}
            </div>
          )}
        </Content>
      </Layout>

      {/* Review Drawer */}
      <Drawer
        title="质量审查报告"
        open={reviewDrawer}
        onClose={() => setReviewDrawer(false)}
        width={560}
      >
        {reviewing ? (
          <div style={{ textAlign: 'center', padding: 40 }}>
            <Spin tip="AI 正在审查申报书质量..." />
          </div>
        ) : (
          <div style={{ whiteSpace: 'pre-wrap', lineHeight: 2, fontSize: 13 }}>
            {project.review_score > 0 && (
              <Typography.Title level={4} style={{ color: project.review_score >= 60 ? '#52c41a' : '#ff4d4f' }}>
                评分：{project.review_score}/100
              </Typography.Title>
            )}
            {reviewResult || '无审查结果'}
          </div>
        )}
      </Drawer>

      {/* Preview Modal */}
      <Modal
        title="文档预览"
        open={previewOpen}
        onCancel={() => setPreviewOpen(false)}
        footer={[
          <Button key="close" onClick={() => setPreviewOpen(false)}>关闭</Button>,
          canExport && (
            <Button key="export" type="primary" icon={<ExportOutlined />} onClick={() => {
              setPreviewOpen(false);
              handleExport();
            }}>
              导出
            </Button>
          ),
        ]}
        width={900}
        style={{ top: 24 }}
      >
        <DocumentPreview projectId={project.id} />
      </Modal>

      <style>{`
        @keyframes blink {
          0%, 50% { opacity: 1; }
          51%, 100% { opacity: 0; }
        }
      `}</style>
    </div>
  );
}
