import { Editor, Extension } from '@tiptap/core'
import StarterKit from '@tiptap/starter-kit'
import { Markdown } from '@tiptap/markdown'
import Suggestion from '@tiptap/suggestion'

// ── スラッシュコマンド定義 ──────────────────────────────────────
const COMMANDS = [
  {
    title: '見出し 1',
    description: '大見出し',
    icon: 'H1',
    command: ({ editor, range }) =>
      editor.chain().focus().deleteRange(range).setHeading({ level: 1 }).run(),
  },
  {
    title: '見出し 2',
    description: '中見出し',
    icon: 'H2',
    command: ({ editor, range }) =>
      editor.chain().focus().deleteRange(range).setHeading({ level: 2 }).run(),
  },
  {
    title: '見出し 3',
    description: '小見出し',
    icon: 'H3',
    command: ({ editor, range }) =>
      editor.chain().focus().deleteRange(range).setHeading({ level: 3 }).run(),
  },
  {
    title: '箇条書き',
    description: 'リスト',
    icon: '•',
    command: ({ editor, range }) =>
      editor.chain().focus().deleteRange(range).toggleBulletList().run(),
  },
  {
    title: '番号リスト',
    description: '番号付きリスト',
    icon: '1.',
    command: ({ editor, range }) =>
      editor.chain().focus().deleteRange(range).toggleOrderedList().run(),
  },
  {
    title: '引用',
    description: 'ブロック引用',
    icon: '❝',
    command: ({ editor, range }) =>
      editor.chain().focus().deleteRange(range).toggleBlockquote().run(),
  },
  {
    title: 'コードブロック',
    description: 'コードの表示',
    icon: '</>',
    command: ({ editor, range }) =>
      editor.chain().focus().deleteRange(range).toggleCodeBlock().run(),
  },
  {
    title: '区切り線',
    description: '水平線を挿入',
    icon: '—',
    command: ({ editor, range }) =>
      editor.chain().focus().deleteRange(range).setHorizontalRule().run(),
  },
  {
    title: 'テキスト',
    description: '通常のテキスト',
    icon: 'T',
    command: ({ editor, range }) =>
      editor.chain().focus().deleteRange(range).setParagraph().run(),
  },
]

// ── スラッシュメニュー UI ──────────────────────────────────────
function createMenu() {
  const el = document.createElement('div')
  el.className = 'slash-menu'
  document.body.appendChild(el)
  return el
}

function renderMenu(menu, items, selectedIndex, onSelect) {
  menu.innerHTML = ''
  if (items.length === 0) {
    menu.style.display = 'none'
    return
  }
  menu.style.display = 'block'
  items.forEach((item, i) => {
    const btn = document.createElement('button')
    btn.type = 'button'
    btn.className = 'slash-menu-item' + (i === selectedIndex ? ' is-selected' : '')
    btn.innerHTML = `
      <span class="slash-menu-icon">${item.icon}</span>
      <span class="slash-menu-label">
        <span class="slash-menu-title">${item.title}</span>
        <span class="slash-menu-desc">${item.description}</span>
      </span>
    `
    btn.addEventListener('mousedown', (e) => {
      e.preventDefault()
      onSelect(item)
    })
    menu.appendChild(btn)
  })
}

function positionMenu(menu, clientRect) {
  if (!clientRect) return
  const rect = typeof clientRect === 'function' ? clientRect() : clientRect
  if (!rect) return
  const scrollY = window.scrollY || document.documentElement.scrollTop
  const scrollX = window.scrollX || document.documentElement.scrollLeft
  menu.style.left = `${rect.left + scrollX}px`
  menu.style.top  = `${rect.bottom + scrollY + 6}px`
}

// ── SlashCommands Extension ──────────────────────────────────────
const SlashCommands = Extension.create({
  name: 'slashCommands',

  addProseMirrorPlugins() {
    return [
      Suggestion({
        editor: this.editor,
        char: '/',
        allowSpaces: false,
        startOfLine: false,

        items: ({ query }) =>
          COMMANDS.filter(
            (c) =>
              c.title.toLowerCase().includes(query.toLowerCase()) ||
              c.description.toLowerCase().includes(query.toLowerCase())
          ).slice(0, 10),

        render: () => {
          let menu = null
          let currentProps = null
          let selectedIndex = 0

          const update = () => {
            if (!menu || !currentProps) return
            renderMenu(menu, currentProps.items, selectedIndex, (item) => {
              item.command({ editor: currentProps.editor, range: currentProps.range })
            })
            positionMenu(menu, currentProps.clientRect)
          }

          return {
            onStart(props) {
              currentProps = props
              selectedIndex = 0
              menu = createMenu()
              update()
            },

            onUpdate(props) {
              currentProps = props
              selectedIndex = 0
              update()
            },

            onKeyDown({ event }) {
              if (!currentProps?.items?.length) return false

              if (event.key === 'ArrowDown') {
                selectedIndex = (selectedIndex + 1) % currentProps.items.length
                update()
                return true
              }
              if (event.key === 'ArrowUp') {
                selectedIndex = (selectedIndex - 1 + currentProps.items.length) % currentProps.items.length
                update()
                return true
              }
              if (event.key === 'Enter') {
                currentProps.items[selectedIndex]?.command({
                  editor: currentProps.editor,
                  range: currentProps.range,
                })
                return true
              }
              if (event.key === 'Escape') {
                menu.style.display = 'none'
                return true
              }
              return false
            },

            onExit() {
              menu?.remove()
              menu = null
              currentProps = null
            },
          }
        },
      }),
    ]
  },
})

// ── エディタ初期化 ──────────────────────────────────────────────
const textarea = document.getElementById('body-editor')
if (textarea) {
  const editorEl = document.createElement('div')
  editorEl.id = 'tiptap-editor'
  textarea.parentNode.insertBefore(editorEl, textarea)
  textarea.style.display = 'none'

  const editor = new Editor({
    element: editorEl,
    extensions: [StarterKit, Markdown, SlashCommands],
    content: textarea.value,
    editorProps: {
      attributes: { class: 'tiptap-content' },
    },
  })

  editor.on('update', () => {
    textarea.value = editor.getMarkdown()
  })

  const form = textarea.closest('form')
  form?.addEventListener('submit', () => {
    textarea.value = editor.getMarkdown()
  })
}
