import { renderHook, act } from '@testing-library/react'
import { useFarmForm } from '../../hooks/useFarmForm'

describe('useFarmForm', () => {
  it('initialises with empty fields and no errors', () => {
    const { result } = renderHook(() => useFarmForm())
    expect(result.current.fields).toEqual({ farmSize: '', lat: '', lng: '' })
    expect(result.current.errors).toEqual({})
    expect(result.current.files).toEqual([])
  })

  it('sets field values via setField', () => {
    const { result } = renderHook(() => useFarmForm())
    act(() => result.current.setField('farmSize')({ target: { value: '100' } }))
    expect(result.current.fields.farmSize).toBe('100')
  })

  it('sets validation errors on invalid submit', () => {
    const { result } = renderHook(() => useFarmForm())
    act(() => result.current.handleSubmit({ preventDefault: () => {} }))
    expect(result.current.errors.farmSize).toBeTruthy()
    expect(result.current.errors.lat).toBeTruthy()
    expect(result.current.errors.lng).toBeTruthy()
    expect(result.current.errors.files).toBeTruthy()
  })

  it('clears errors on valid submit', () => {
    const { result } = renderHook(() => useFarmForm())
    act(() => {
      result.current.setField('farmSize')({ target: { value: '100' } })
      result.current.setField('lat')({ target: { value: '41.5' } })
      result.current.setField('lng')({ target: { value: '-87.5' } })
      result.current.setFiles([new File(['x'], 'test.txt')])
    })
    act(() => result.current.handleSubmit({ preventDefault: () => {} }))
    expect(result.current.errors).toEqual({})
  })
})
