import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import App from '../App'

describe('FarmForm', () => {
  it('renders all form fields', () => {
    render(<App />)
    expect(screen.getByLabelText(/farm size/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/latitude/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/longitude/i)).toBeInTheDocument()
    expect(screen.getByLabelText(/files/i)).toBeInTheDocument()
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
    await userEvent.type(screen.getByLabelText(/latitude/i), '999')
    await userEvent.click(screen.getByRole('button', { name: /submit/i }))
    expect(screen.getByText(/valid latitude/i)).toBeInTheDocument()
  })

  it('rejects out-of-range longitude', async () => {
    render(<App />)
    await userEvent.type(screen.getByLabelText(/longitude/i), '999')
    await userEvent.click(screen.getByRole('button', { name: /submit/i }))
    expect(screen.getByText(/valid longitude/i)).toBeInTheDocument()
  })

  it('clears field errors when values become valid', async () => {
    render(<App />)
    await userEvent.click(screen.getByRole('button', { name: /submit/i }))
    expect(screen.getByText(/valid farm size/i)).toBeInTheDocument()

    await userEvent.type(screen.getByLabelText(/farm size/i), '100')
    await userEvent.type(screen.getByLabelText(/latitude/i), '41.5')
    await userEvent.type(screen.getByLabelText(/longitude/i), '-87.5')
    await userEvent.click(screen.getByRole('button', { name: /submit/i }))

    expect(screen.queryByText(/valid farm size/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/valid latitude/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/valid longitude/i)).not.toBeInTheDocument()
  })
})
