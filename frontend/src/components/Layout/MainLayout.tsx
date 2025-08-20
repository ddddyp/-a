'use client';

import React, { useState } from 'react';
import { Layout, Menu, Avatar, Dropdown, Button, Space } from 'antd';
import {
  DashboardOutlined,
  DatabaseOutlined,
  ExperimentOutlined,
  UnorderedListOutlined,
  BarChartOutlined,
  UserOutlined,
  LogoutOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
} from '@ant-design/icons';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '@/contexts/AuthContext';
import type { MenuProps } from 'antd';

const { Header, Sider, Content } = Layout;

interface MainLayoutProps {
  children: React.ReactNode;
}

export default function MainLayout({ children }: MainLayoutProps) {
  const [collapsed, setCollapsed] = useState(false);
  const { user, logout } = useAuth();
  const router = useRouter();
  const pathname = usePathname();

  // 侧边栏菜单项
  const menuItems: MenuProps['items'] = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/datasets',
      icon: <DatabaseOutlined />,
      label: '数据集管理',
    },
    {
      key: '/analysis',
      icon: <ExperimentOutlined />,
      label: '分析任务',
    },
    {
      key: '/tasks',
      icon: <UnorderedListOutlined />,
      label: '任务监控',
    },
    {
      key: '/results',
      icon: <BarChartOutlined />,
      label: '结果展示',
    },
  ];

  // 用户下拉菜单
  const userMenuItems: MenuProps['items'] = [
    {
      key: 'profile',
      icon: <UserOutlined />,
      label: '个人信息',
    },
    {
      type: 'divider',
    },
    {
      key: 'logout',
      icon: <LogoutOutlined />,
      label: '退出登录',
      onClick: () => {
        logout();
        router.push('/login');
      },
    },
  ];

  const handleMenuClick = ({ key }: { key: string }) => {
    router.push(key);
  };

  return (
    <Layout className="min-h-screen">
      <Sider 
        trigger={null} 
        collapsible 
        collapsed={collapsed}
        theme="light"
        width={220}
        className="custom-sider"
      >

        <Menu
          theme="light"
          mode="inline"
          selectedKeys={[pathname]}
          items={menuItems}
          onClick={handleMenuClick}
          className="custom-menu"
        />
      </Sider>
      
      <Layout>
        <Header className="bg-white px-4 flex items-center justify-between shadow-sm">
          <Button
            type="text"
            icon={collapsed ? <MenuUnfoldOutlined /> : <MenuFoldOutlined />}
            onClick={() => setCollapsed(!collapsed)}
            className="text-base"
          />
          
          <Space>
            <span className="text-gray-600">欢迎，{user?.username}</span>
            <Dropdown menu={{ items: userMenuItems }} placement="bottomRight">
              <Avatar 
                icon={<UserOutlined />} 
                className="cursor-pointer bg-blue-500"
              />
            </Dropdown>
          </Space>
        </Header>
        
        <Content className="m-6 p-6 bg-white">
          {children}
        </Content>
      </Layout>
    </Layout>
  );
}