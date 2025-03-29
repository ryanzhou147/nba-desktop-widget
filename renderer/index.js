const information = document.getElementById('info')
information.innerText = `This app is using Chrome (v${window.versions.chrome()}), Node.js (v${window.versions.node()}), and Electron (v${window.versions.electron()})`
const func = async () => {
  const response = await window.versions.ping()
  console.log(response) // prints out 'pong'
}

func()

const syncButton = document.getElementById('syncTabs');
const openButton = document.getElementById('openTabs');
const viewButton = document.getElementById('viewTabs');
const statusDiv = document.getElementById('status');
const serverUrlInput = document.getElementById('serverUrl');
const saveSettingsButton = document.getElementById('saveSettings');