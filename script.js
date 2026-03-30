const statusList = document.getElementById("status-list");
const reqCount = document.getElementById("req-count");
const successRate = document.getElementById("success-rate");
const refreshBtn = document.getElementById("refresh-btn");
const lastRefresh = document.getElementById("last-refresh");

const systemStatus = [
  "API 网关：正常",
  "向量数据库：正常",
  "模型服务：正常",
  "告警系统：正常"
];

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function renderStatus() {
  statusList.innerHTML = "";
  for (const item of systemStatus) {
    const li = document.createElement("li");
    li.textContent = item;
    statusList.appendChild(li);
  }
}

function refreshMetrics() {
  const requests = randomInt(800, 2500);
  const success = (Math.random() * 3 + 97).toFixed(2);

  reqCount.textContent = requests.toLocaleString("zh-CN");
  successRate.textContent = `${success}%`;
  lastRefresh.textContent = `最近刷新：${new Date().toLocaleString("zh-CN")}`;
}

refreshBtn.addEventListener("click", refreshMetrics);

renderStatus();
refreshMetrics();
