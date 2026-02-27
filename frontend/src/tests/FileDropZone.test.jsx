import { render, screen, fireEvent } from '@testing-library/react'
import { useState } from 'react'
import FileDropZone from '../components/FileDropZone'

function Wrapper() {
  const [files, setFiles] = useState([])
  return <FileDropZone files={files} onChange={setFiles} />
}

const makeFile = (name, content = 'x') =>
  new File([content], name, { type: 'text/plain' })

describe('FileDropZone', () => {
  it('renders the drop prompt', () => {
    render(<Wrapper />)
    expect(screen.getByText(/drop files here/i)).toBeInTheDocument()
  })

  it('applies dragging class on dragover', () => {
    render(<Wrapper />)
    const label = screen.getByText(/drop files here/i).closest('label')
    fireEvent.dragOver(label)
    expect(label).toHaveClass('dragging')
    expect(screen.getByText(/release to drop/i)).toBeInTheDocument()
  })

  it('removes dragging class on drag leave', () => {
    render(<Wrapper />)
    const label = screen.getByText(/drop files here/i).closest('label')
    fireEvent.dragOver(label)
    fireEvent.dragLeave(label)
    expect(label).not.toHaveClass('dragging')
  })

  it('lists dropped files', () => {
    render(<Wrapper />)
    const label = screen.getByText(/drop files here/i).closest('label')
    fireEvent.drop(label, { dataTransfer: { files: [makeFile('report.csv')] } })
    expect(screen.getByText('report.csv')).toBeInTheDocument()
  })

  it('does not add duplicate files', () => {
    render(<Wrapper />)
    const label = screen.getByText(/drop files here/i).closest('label')
    const file = makeFile('dup.txt')
    fireEvent.drop(label, { dataTransfer: { files: [file] } })
    fireEvent.drop(label, { dataTransfer: { files: [file] } })
    expect(screen.getAllByText('dup.txt')).toHaveLength(1)
  })

  it('removes a file when ✕ is clicked', () => {
    render(<Wrapper />)
    const label = screen.getByText(/drop files here/i).closest('label')
    fireEvent.drop(label, { dataTransfer: { files: [makeFile('remove-me.txt')] } })
    fireEvent.click(screen.getByTitle('Remove'))
    expect(screen.queryByText('remove-me.txt')).not.toBeInTheDocument()
  })
})
