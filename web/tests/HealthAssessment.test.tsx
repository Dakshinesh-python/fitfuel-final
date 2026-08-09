import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import HealthAssessment from '../src/pages/HealthAssessment';

describe('HealthAssessment', () => {
  it('renders the key form fields', () => {
    render(
      <MemoryRouter>
        <HealthAssessment />
      </MemoryRouter>,
    );

    expect(screen.getByPlaceholderText('75')).toBeInTheDocument();
    expect(screen.getByPlaceholderText('68')).toBeInTheDocument();
    expect(screen.getByRole('combobox', { name: /activity level/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /primary goal/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /dietary preference/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /allergies & restrictions/i })).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /daily budget/i })).toBeInTheDocument();
  });
});
