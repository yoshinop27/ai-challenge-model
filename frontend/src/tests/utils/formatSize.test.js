import { formatSize } from '../../utils/formatSize'

describe('formatSize', () => {
  it('formats bytes', () => expect(formatSize(512)).toBe('512 B'))
  it('formats kilobytes', () => expect(formatSize(2048)).toBe('2.0 KB'))
  it('formats megabytes', () => expect(formatSize(1.5 * 1024 ** 2)).toBe('1.5 MB'))
  it('formats 0 bytes', () => expect(formatSize(0)).toBe('0 B'))
})
