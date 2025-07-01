import type { Preview } from '@storybook/react';
import { withThemeFromJSXProvider } from '@storybook/addon-themes';

// Import global styles
import '../src/app/[locale]/globals.css';

const preview: Preview = {
  parameters: {
    controls: {
      matchers: {
        color: /(background|color)$/i,
        date: /Date$/i,
      },
    },
    layout: 'fullscreen',
  },
  decorators: [
    withThemeFromJSXProvider({
      themes: {
        light: 'light',
        dark: 'dark',
      },
      defaultTheme: 'light',
      Provider: ({ theme, children }) => (
        <div className={theme} style={{ minHeight: '100vh' }}>
          {children}
        </div>
      ),
    }),
  ],
};

export default preview;