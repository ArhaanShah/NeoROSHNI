/// <reference types="vitest/globals" />
/// <reference types="@testing-library/jest-dom" />

import { render, screen } from '@testing-library/react';
import App from './App';

describe('App', () => {
  it('renders app title', () => {
    render(<App />);

    expect(screen.getByText('NeoROSHNI')).toBeInTheDocument();
  });
});
