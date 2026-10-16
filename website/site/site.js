// Orbit UI 官网：实时预览缩放、分段切换、复制代码、入场动效

// <div class="preview" data-src="..." data-viewport="1280x800" data-height="auto|420">
function layoutPreviews() {
  document.querySelectorAll(".preview").forEach(box => {
    let f = box.querySelector("iframe");
    if (!f) {
      f = document.createElement("iframe");
      f.loading = "lazy";
      f.tabIndex = -1;
      f.setAttribute("aria-hidden", "true");
      f.src = box.dataset.src;
      box.appendChild(f);
    }
    const [w, h] = (box.dataset.viewport || "1280x800").split("x").map(Number);
    const bw = box.clientWidth;
    const fixed = Number(box.dataset.height);
    const bh = fixed || bw * h / w;
    const scale = Math.min(bw / w, bh / h);
    f.style.width = w + "px";
    f.style.height = h + "px";
    f.style.transform = `scale(${scale})`;
    f.style.left = Math.max(0, (bw - w * scale) / 2) + "px";
    box.style.height = bh + "px";
  });
}
// 只观察预览框本身：改的是高度，宽度不变，不会形成观察循环
const ro = new ResizeObserver(layoutPreviews);
document.querySelectorAll(".preview").forEach(box => ro.observe(box));
layoutPreviews();

// 分段切换：<div class="o-tabs" data-group="x"><button data-value="a" aria-selected>
document.querySelectorAll(".o-tabs[data-group]").forEach(tabs => {
  tabs.addEventListener("click", e => {
    const b = e.target.closest("button[data-value]");
    if (!b) return;
    tabs.querySelectorAll("button").forEach(x => x.setAttribute("aria-selected", String(x === b)));
    document.dispatchEvent(new CustomEvent("tab:" + tabs.dataset.group, { detail: b.dataset.value }));
  });
});

// 复制代码块
document.querySelectorAll(".code-wrap").forEach(wrap => {
  const btn = document.createElement("button");
  btn.className = "copy";
  btn.type = "button";
  btn.textContent = "复制";
  btn.onclick = async () => {
    try {
      await navigator.clipboard.writeText(wrap.querySelector("pre").innerText.trim());
      btn.textContent = "已复制";
    } catch {
      btn.textContent = "请手动复制";
    }
    setTimeout(() => (btn.textContent = "复制"), 1600);
  };
  wrap.prepend(btn);
});

// 入场：每个 .reveal 进入视口时出现一次
const io = new IntersectionObserver(entries => {
  entries.forEach(en => {
    if (en.isIntersecting) { en.target.classList.add("in"); io.unobserve(en.target); }
  });
}, { rootMargin: "0px 0px -8% 0px" });
document.querySelectorAll(".reveal").forEach(el => io.observe(el));
