import type { Meta, StoryObj } from '@storybook/react';
import { fn } from '@storybook/test';
import { Input } from '../../components/ui/input';
import { InputWithIcon } from '../../components/ui/input-with-icon';
import { Button } from '../../components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '../../components/ui/card';

const meta = {
  title: 'UI/Form Controls',
  parameters: {
    layout: 'centered',
    docs: {
      description: {
        component: 'A collection of form input components with various styles and features.',
      },
    },
  },
  tags: ['autodocs'],
} satisfies Meta;

export default meta;
type Story = StoryObj<typeof meta>;

export const BasicInput: Story = {
  render: () => (
    <div className="w-[300px] space-y-4">
      <div>
        <label className="text-sm font-medium mb-2 block">Default Input</label>
        <Input placeholder="Enter your email" />
      </div>
      <div>
        <label className="text-sm font-medium mb-2 block">Password Input</label>
        <Input type="password" placeholder="Enter your password" />
      </div>
      <div>
        <label className="text-sm font-medium mb-2 block">Disabled Input</label>
        <Input placeholder="Disabled input" disabled />
      </div>
    </div>
  ),
};

export const InputVariants: Story = {
  render: () => (
    <div className="w-[300px] space-y-4">
      <div>
        <label className="text-sm font-medium mb-2 block">Default</label>
        <Input placeholder="Default input" variant="default" />
      </div>
      <div>
        <label className="text-sm font-medium mb-2 block">Error State</label>
        <Input placeholder="Error input" variant="error" />
        <p className="text-sm text-red-500 mt-1">This field is required</p>
      </div>
      <div>
        <label className="text-sm font-medium mb-2 block">Success State</label>
        <Input placeholder="Success input" variant="success" />
        <p className="text-sm text-green-600 mt-1">Email is available</p>
      </div>
    </div>
  ),
};

export const InputWithIcons: Story = {
  render: () => (
    <div className="w-[300px] space-y-4">
      <div>
        <label className="text-sm font-medium mb-2 block">Email with Icon</label>
        <InputWithIcon 
          type="email"
          placeholder="Enter your email" 
          leftIcon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
            </svg>
          }
        />
      </div>
      <div>
        <label className="text-sm font-medium mb-2 block">Search with Icon</label>
        <InputWithIcon 
          placeholder="Search..." 
          leftIcon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          }
          rightIcon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          }
          onRightIconClick={fn()}
        />
      </div>
      <div>
        <label className="text-sm font-medium mb-2 block">Password with Toggle</label>
        <InputWithIcon 
          type="password"
          placeholder="Enter password" 
          rightIcon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
            </svg>
          }
          onRightIconClick={fn()}
        />
      </div>
    </div>
  ),
};

export const LoginForm: Story = {
  render: () => (
    <Card className="w-[400px]">
      <CardHeader>
        <CardTitle>Login to Your Account</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <label className="text-sm font-medium mb-2 block">Email</label>
          <InputWithIcon 
            type="email"
            placeholder="Enter your email" 
            leftIcon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 12a4 4 0 10-8 0 4 4 0 008 0zm0 0v1.5a2.5 2.5 0 005 0V12a9 9 0 10-9 9m4.5-1.206a8.959 8.959 0 01-4.5 1.207" />
              </svg>
            }
          />
        </div>
        <div>
          <label className="text-sm font-medium mb-2 block">Password</label>
          <InputWithIcon 
            type="password"
            placeholder="Enter your password" 
            leftIcon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            }
            rightIcon={
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z" />
              </svg>
            }
            onRightIconClick={fn()}
          />
        </div>
        <div className="flex items-center justify-between">
          <label className="flex items-center space-x-2 text-sm">
            <input type="checkbox" className="rounded" />
            <span>Remember me</span>
          </label>
          <Button variant="link" className="p-0 h-auto">
            Forgot password?
          </Button>
        </div>
        <Button className="w-full">Sign In</Button>
        <div className="text-center">
          <span className="text-sm text-gray-600">Don't have an account? </span>
          <Button variant="link" className="p-0 h-auto">
            Sign up
          </Button>
        </div>
      </CardContent>
    </Card>
  ),
};

export const SearchForm: Story = {
  render: () => (
    <div className="w-[500px] space-y-4">
      <div className="flex space-x-2">
        <InputWithIcon 
          placeholder="Search for anything..." 
          className="flex-1"
          leftIcon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
            </svg>
          }
          rightIcon={
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 100 4m0-4v2m0-6V4" />
            </svg>
          }
          onRightIconClick={fn()}
        />
        <Button>Search</Button>
      </div>
      <div className="text-sm text-gray-500">
        Use filters to narrow down your search results
      </div>
    </div>
  ),
};