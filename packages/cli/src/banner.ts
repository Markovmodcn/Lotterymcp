const GLYPHS = {
  N: [
    '███╗   ██╗',
    '████╗  ██║',
    '██╔██╗ ██║',
    '██║╚██╗██║',
    '██║ ╚████║',
    '╚═╝  ╚═══╝',
  ],
  E: [
    '███████╗',
    '██╔════╝',
    '█████╗  ',
    '██╔══╝  ',
    '███████╗',
    '╚══════╝',
  ],
  U: [
    '██╗   ██╗',
    '██║   ██║',
    '██║   ██║',
    '██║   ██║',
    '╚██████╔╝',
    ' ╚═════╝ ',
  ],
  X: [
    '██╗  ██╗',
    '╚██╗██╔╝',
    ' ╚███╔╝ ',
    ' ██╔██╗ ',
    '██╔╝╚██╗',
    '╚═╝  ╚═╝',
  ],
  S: [
    '███████╗',
    '██╔════╝',
    '███████╗',
    '╚════██║',
    '███████║',
    '╚══════╝',
  ],
  B: [
    '██████╗ ',
    '██╔══██╗',
    '██████╔╝',
    '██╔══██╗',
    '██████╔╝',
    '╚═════╝ ',
  ],
  O: [
    ' ██████╗ ',
    '██╔═══██╗',
    '██║   ██║',
    '██║   ██║',
    '╚██████╔╝',
    ' ╚═════╝ ',
  ],
  T: [
    '████████╗',
    '╚══██╔══╝',
    '   ██║   ',
    '   ██║   ',
    '   ██║   ',
    '   ╚═╝   ',
  ],
} as const

const WORD = 'NEUXSBOT'
const SUBTITLE_LINE = 'NEUXSBOT 彩票分析命令行'
const WEBSITE_LINE = 'www.neuxsbot.com'

const buildWordmarkLines = () => {
  const rows = Array.from({ length: 6 }, () => '')

  for (const character of WORD) {
    const glyph = GLYPHS[character as keyof typeof GLYPHS]
    for (let index = 0; index < rows.length; index += 1) {
      rows[index] += `${glyph[index]}  `
    }
  }

  return rows.map((line) => line.trimEnd())
}

const WORDMARK_LINES = buildWordmarkLines()

const shadowify = (value: string) => value.replace(/[^\s]/g, '░')

const centerText = (value: string, width: number) => {
  const padding = Math.max(0, Math.floor((width - value.length) / 2))
  return `${' '.repeat(padding)}${value}`
}

export const shouldShowBanner = (
  command: string | undefined,
  stream: Pick<NodeJS.WriteStream, 'isTTY'> = process.stdout,
) => {
  if (command === 'serve') {
    return false
  }

  if (process.env.NBCP_DISABLE_BANNER === '1') {
    return false
  }

  if (process.env.NBCP_FORCE_BANNER === '1') {
    return true
  }

  return Boolean(stream.isTTY)
}

export const renderNbcpBanner = (
  _stream: Pick<NodeJS.WriteStream, 'isTTY'> = process.stdout,
) => {
  const maxWidth = Math.max(
    ...WORDMARK_LINES.map((line) => line.length),
    SUBTITLE_LINE.length,
    WEBSITE_LINE.length,
  )

  const renderedLines = WORDMARK_LINES.flatMap((line) => [
    ` ${shadowify(line)}`,
    line,
  ])

  return [
    '',
    ...renderedLines,
    '',
    centerText(SUBTITLE_LINE, maxWidth),
    centerText(WEBSITE_LINE, maxWidth),
    '',
  ].join('\n')
}
