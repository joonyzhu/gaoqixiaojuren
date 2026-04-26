import { Routes, Route, useNavigate, useLocation } from 'react-router-dom';
import { Layout, Menu, Typography } from 'antd';
import {
  DashboardOutlined,
  FileTextOutlined,
  FolderOpenOutlined,
  SettingOutlined,
  AppstoreOutlined,
} from '@ant-design/icons';
import Dashboard from './pages/Dashboard';
import ProjectWorkspace from './pages/ProjectWorkspace';
import Materials from './pages/Materials';
import Settings from './pages/Settings';

const { Header, Sider, Content } = Layout;

const menuItems = [
  { key: '/', icon: <DashboardOutlined />, label: '项目总览' },
  { key: '/project', icon: <FileTextOutlined />, label: '申报工作台' },
  { key: '/materials', icon: <FolderOpenOutlined />, label: '材料库' },
  { key: '/settings', icon: <SettingOutlined />, label: '系统设置' },
];

function App() {
  const navigate = useNavigate();
  const location = useLocation();

  const currentPath = location.pathname === '/' ? '/' : `/${location.pathname.split('/')[1]}`;

  return (
    <Layout style={{ minHeight: '100vh' }}>
      <Header style={{
        display: 'flex',
        alignItems: 'center',
        padding: '0 24px',
        background: '#001529',
      }}>
        <AppstoreOutlined style={{ fontSize: 24, color: '#fff', marginRight: 12 }} />
        <Typography.Title level={4} style={{ color: '#fff', margin: 0 }}>
          高企&amp;小巨人智能申报系统
        </Typography.Title>
      </Header>
      <Layout hasSider>
        <Sider width={220} style={{ background: '#fff' }}>
          <Menu
            mode="inline"
            selectedKeys={[currentPath]}
            items={menuItems}
            onClick={({ key }) => navigate(key)}
            style={{ height: '100%', borderRight: 0 }}
          />
        </Sider>
        <Content style={{ padding: 24, background: '#f5f5f5' }}>
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/project/:id?" element={<ProjectWorkspace />} />
            <Route path="/materials" element={<Materials />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Content>
      </Layout>
    </Layout>
  );
}

export default App;
