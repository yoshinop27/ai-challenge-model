import { render, screen, fireEvent } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../App'

describe('FarmForm', () => {
  it('renders all form fields', () => {
    render(<App />)
    expect(screen.getByPlaceholderText(/250/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/41\.8781/)).toBeInTheDocument()
    expect(screen.getByPlaceholderText(/−87\.6298/)).toBeInTheDocument()
    expect(screen.getByText(/drop files here/i)).toBeInTheDocument()
  })

  it('shows validation errors on empty submit', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: /submit/i }))
    expect(screen.getByText(/valid farm size/i)).toBeInTheDocument()
    expect(screen.getByText(/valid latitude/i)).toBeInTheDocument()
    expect(screen.getByText(/valid longitude/i)).toBeInTheDocument()
    expect(screen.getByText(/upload at least one file/i)).toBeInTheDocument()
  })

  it('rejects out-of-range latitude', async () => {
    render(<App />)
    await userEvent.type(screen.getByPlaceholderText(/41\.8781/), '999')
    await userEvent.click(screen.getByRole('button', { name: /submit/i }))
    expect(screen.getByText(/valid latitude/i)).toBeInTheDocument()
  })

  it('rejects out-of-range longitude', async () => {
    render(<App />)
    await userEvent.type(screen.getByPlaceholderText(/−87\.6298/), '999')
    await userEvent.click(screen.getByRole('button', { name: /submit/i }))
    expect(screen.getByText(/valid longitude/i)).toBeInTheDocument()
  })

  it('clears field errors when values become valid', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: /submit/i }))
    expect(screen.getByText(/valid farm size/i)).toBeInTheDocument()

    await userEvent.type(screen.getByPlaceholderText(/250/), '100')
    await userEvent.type(screen.getByPlaceholderText(/41\.8781/), '41.5')
    await userEvent.type(screen.getByPlaceholderText(/−87\.6298/), '-87.5')
    await userEvent.click(screen.getByRole('button', { name: /submit/i }))

    expect(screen.queryByText(/valid farm size/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/valid latitude/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/valid longitude/i)).not.toBeInTheDocument()
  })
})
