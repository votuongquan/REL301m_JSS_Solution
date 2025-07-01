# Storybook for EntervIU Frontend

This Storybook contains all the UI components, animations, and page sections for the EntervIU frontend application.

## 🚀 Getting Started

### Prerequisites

Make sure you have the following installed:
- Node.js (v18 or higher)
- npm, yarn, or pnpm

### Installation

1. Install dependencies:
```bash
cd frontend
npm install
# or
yarn install
# or
pnpm install
```

2. Start Storybook:
```bash
npm run storybook
# or
yarn storybook
# or
pnpm storybook
```

3. Open your browser and navigate to `http://localhost:6006`

## 📁 Project Structure

```
frontend/
├── .storybook/           # Storybook configuration
│   ├── main.ts          # Main configuration
│   └── preview.ts       # Preview configuration with themes
├── src/
│   ├── components/      # All React components
│   │   ├── ui/         # Basic UI components (Button, Card, Input, etc.)
│   │   ├── animations/ # Animation components (FallingText, MagneticCard, etc.)
│   │   ├── layout/     # Layout components (Header, Footer, etc.)
│   │   └── ...
│   └── stories/        # Storybook stories
│       ├── Introduction.mdx    # Welcome page
│       ├── ui/                # UI component stories
│       ├── animations/        # Animation component stories
│       └── examples/          # Complex example stories
```

## 🎨 Component Categories

### UI Components
- **Button** - Various button variants and sizes
- **Card** - Flexible card components with header, content, and footer
- **Form Controls** - Input fields, dropdowns, and form elements

### Animations
- **FallingText** - Text animations with multiple motion variants
- **MagneticCard** - Interactive cards that follow mouse movement
- **ScrollReveal** - Components that animate on scroll

### Examples
- **Landing Page** - Complete page sections showcasing multiple components

## 🛠 Available Addons

- **Controls** - Dynamically interact with component props
- **Docs** - Auto-generated documentation for components
- **Actions** - View component interactions and events
- **Themes** - Switch between light and dark themes
- **Links** - Navigate between related stories

## 🎨 Theming

This Storybook supports both light and dark themes. You can switch between themes using the theme toggle in the toolbar.

### Custom CSS Variables

The project uses CSS custom properties for consistent theming:

```css
:root {
  --background: #ffffff;
  --foreground: #171717;
  --primary: #3b82f6;
  --secondary: #f1f5f9;
  /* ... and many more */
}
```

### Dark Mode

Dark mode is automatically supported through CSS custom properties and the `[data-theme=dark]` selector.

## 📖 Writing Stories

### Basic Story Structure

```typescript
import type { Meta, StoryObj } from '@storybook/react';
import { YourComponent } from '../components/YourComponent';

const meta = {
  title: 'Category/YourComponent',
  component: YourComponent,
  parameters: {
    layout: 'centered',
  },
  tags: ['autodocs'],
  argTypes: {
    // Define controls for component props
  },
} satisfies Meta<typeof YourComponent>;

export default meta;
type Story = StoryObj<typeof meta>;

export const Default: Story = {
  args: {
    // Default props
  },
};
```

### Story Categories

- `UI/` - Basic UI components
- `Animations/` - Animation components
- `Layout/` - Layout and navigation components
- `Examples/` - Complex examples and page sections

## 🔧 Configuration

### Main Configuration (.storybook/main.ts)

- Uses `@storybook/nextjs` framework for Next.js compatibility
- Configured for TypeScript with `react-docgen-typescript`
- Includes essential addons for development

### Preview Configuration (.storybook/preview.ts)

- Imports global CSS styles
- Configures theme switching
- Sets up decorators for consistent styling

## 🚀 Building for Production

To build Storybook for production:

```bash
npm run build-storybook
# or
yarn build-storybook
# or
pnpm build-storybook
```

This creates a static version of your Storybook in the `storybook-static` directory.

## 📚 Useful Resources

- [Storybook Documentation](https://storybook.js.org/docs)
- [Next.js Integration](https://storybook.js.org/docs/get-started/frameworks/nextjs)
- [Writing Stories](https://storybook.js.org/docs/writing-stories)
- [Storybook Addons](https://storybook.js.org/addons)

## 🤝 Contributing

When adding new components:

1. Create the component in the appropriate directory under `src/components/`
2. Write comprehensive stories in `src/stories/`
3. Include proper documentation and controls
4. Test both light and dark themes
5. Add examples showing different use cases

## 🎯 Best Practices

- **Use descriptive story names** that clearly indicate the component state or variant
- **Include comprehensive controls** for all important props
- **Write good documentation** in the component's docstring
- **Test accessibility** using the a11y addon
- **Include realistic examples** that show real-world usage
- **Group related stories** logically within categories

## 🐛 Troubleshooting

### Common Issues

1. **CSS not loading**: Make sure the correct path is set in `preview.ts`
2. **Components not found**: Check import paths and component exports
3. **Theme not working**: Verify CSS custom properties are properly defined
4. **TypeScript errors**: Ensure all types are properly imported and defined

### Getting Help

- Check the [Storybook Discord](https://discord.gg/storybook)
- Browse [Storybook GitHub Issues](https://github.com/storybookjs/storybook/issues)
- Review the [Storybook Documentation](https://storybook.js.org/docs)