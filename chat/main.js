console.log('Hello world!')

// за потреби змінюємо на сокет з LiveServer
const ws = new WebSocket('ws://localhost:8080')
// const ws = new WebSocket('ws://127.0.0.1:5500')

formChat.addEventListener('submit', (e) => {
  e.preventDefault()
  ws.send(textField.value) //ось цей текст приходить в рядок (e.data)
  textField.value = null
})

ws.onopen = (e) => {
  console.log('WebSocket connect!')
}

ws.onmessage = (e) => {
  console.log(e.data)
  const text = e.data
  // console.log('Message received:', e.data)

  const elMsg = document.createElement('div')
  elMsg.textContent = text
  subscribe.appendChild(elMsg)
}