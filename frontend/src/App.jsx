import { useEffect, useRef, useState } from "react"
import "./index.css"

// dynamic script loader
function loadScript(src) {
  return new Promise((resolve, reject) => {
    if (document.querySelector(`script[src="${src}"]`)) return resolve()
    const s = document.createElement("script")
    s.src = src
    s.async = true
    s.onload = () => resolve()
    s.onerror = reject
    document.body.appendChild(s)
  })
}

function LLMCard({ title, author, extraClass = "", theme }) {
  const [step, setStep] = useState("front")
  const [file, setFile] = useState(null)
  const [progress, setProgress] = useState(0)
  const vantaRef = useRef(null)
  const vantaInstanceRef = useRef(null)


  useEffect(() => {
    if (step === "progress") {
      let v = 0
      const i = setInterval(() => {
        v += 10
        setProgress(v)
        if (v >= 100) {
          clearInterval(i)
          setStep("download")
        }
      }, 300)
      return () => clearInterval(i)
    }
  }, [step])

  const handleFileUpload = (e) => {
    const uploaded = e.target.files[0]
    if (uploaded) {
      setFile(uploaded)
      setStep("progress")
    }
  }

  const resetCard = () => {
    setStep("front")
    setFile(null)
    setProgress(0)
  }


  // theme colors for backgrounds
  const themeMap = {
    "light-theme": {
      llama: { highlight: "#0064E0", midtone: "#4F9DFC", lowlight: "#D4C4E2", base: "#ffffff" },
      mistral: { color2: "#e00400" },
    },
    "paper-theme": {
      llama: { highlight: "#AEDDF4", midtone: "#D6C6E6", lowlight: "#87F2C0", base: "#fffaf0" },
      mistral: { color2: "#ffae00" },
    },
    "dark-theme": {
      llama: { highlight: "#05073A", midtone: "#563673", lowlight: "#BFA4B4", base: "#000000" },
      mistral: { color2: "#76b900" },
    },
  }
  const colors = themeMap[theme] || themeMap["light-theme"]

  // BUTTON TEXT color per theme (Req #1)
  const buttonTextColor = theme === "dark-theme" ? "#FFFFFF" : "#000000"

  // Vanta init
  useEffect(() => {
    let cancelled = false
    async function initVanta() {
      await loadScript("https://unpkg.com/three@0.134.0/build/three.min.js")
      await loadScript("https://unpkg.com/vanta@latest/dist/vanta.fog.min.js")
      await loadScript("https://unpkg.com/vanta@latest/dist/vanta.cells.min.js")

      if (cancelled) return
      if (vantaInstanceRef.current?.destroy) vantaInstanceRef.current.destroy()

      if (window.VANTA) {
        if (extraClass === "llama" && window.VANTA.FOG) {
          vantaInstanceRef.current = window.VANTA.FOG({
            el: vantaRef.current,
            mouseControls: true,
            touchControls: true,
            gyroControls: false,
            minHeight: 200.0,
            minWidth: 200.0,
            highlightColor: colors.llama.highlight,
            midtoneColor: colors.llama.midtone,
            lowlightColor: colors.llama.lowlight,
            baseColor: colors.llama.base,
            blurFactor: 0.65,
            speed: 3.0,
            zoom: 1.5,
          })
        }
        if (extraClass === "mistral" && window.VANTA.CELLS) {
          const c2 = colors.mistral?.color2 || "#e00400"
          let color2Int = 0xe00400
          try {
            color2Int = parseInt(c2.slice(1), 16)
          } catch (err) {
            color2Int = 0xe00400
          }
          vantaInstanceRef.current = window.VANTA.CELLS({
            el: vantaRef.current,
            mouseControls: true,
            touchControls: true,
            gyroControls: false,
            minHeight: 200.0,
            minWidth: 200.0,
            scale: 1.0,
            color1: 0x000000,
            color2: color2Int,
            size: 2.0,
            speed: 2.0,
          })
        }
      }
    }
    if (extraClass === "llama" || extraClass === "mistral") initVanta()
    return () => {
      cancelled = true
      if (vantaInstanceRef.current?.destroy) vantaInstanceRef.current.destroy()
    }
  }, [theme, extraClass])

  return (
    <div className={`llm-card ${extraClass}`}>
      {(extraClass === "llama" || extraClass === "mistral") && (
        <div ref={vantaRef} className="vanta-bg" aria-hidden="true" style={{ position: "absolute", inset: 0, zIndex: 0 }} />
      )}

      <div className="card-content" style={{ position: "relative", zIndex: 1 }}>
        {step === "front" && (
          <div className="card-face card-front">
            {/* Req: Only Mistral headings forced white */}
            <h2 style={{ color: extraClass === "mistral" ? "#FFFFFF" : undefined }}>{title}</h2>
            <h5 style={{ color: extraClass === "mistral" ? "#FFFFFF" : undefined }}>by</h5>
            <h4 style={{ color: extraClass === "mistral" ? "#FFFFFF" : undefined }}>{author}</h4>

            <button className="upload-btn" style={{ color: buttonTextColor }} onClick={() => setStep("upload")}>
              Start
            </button>
          </div>
        )}

        {step === "upload" && (
          <div className="card-face card-back upload-section">
            <input type="file" accept=".pdf" id={`${title}-file`} style={{ display: "none" }} onChange={handleFileUpload} />
            <label htmlFor={`${title}-file`} className="upload-btn" style={{ color: buttonTextColor }}>
              Upload PDF
            </label>
            <button className="go-back-btn" style={{ color: buttonTextColor }} onClick={resetCard}>
              ⬅ Back
            </button>
          </div>
        )}

        {step === "progress" && (
          <div className="card-face card-back download-section">
            <div className="progress-container">
              <div className="progress-bar" style={{ width: `${progress}%` }} />
            </div>
            <p>Processing {file?.name}...</p>
          </div>
        )}

        {step === "download" && (
          <div className="card-face card-back download-section">
            <button className="download-btn" style={{ color: buttonTextColor }} onClick={}>
              Download Result
            </button>
            <p>{file?.name?.replace?.(".pdf", "_summary.pdf")}</p>
            <button className="go-back-btn" style={{ color: buttonTextColor }} onClick={resetCard}>
              ⬅ Reset
            </button>
          </div>
        )}
      </div>
    </div>
  )
}

// ========================================================
// App root
// ========================================================
export default function App() {
  const [theme, setTheme] = useState("light-theme")

  useEffect(() => {
    document.body.classList.remove("light-theme", "dark-theme", "paper-theme")
    document.body.classList.add(theme)
  }, [theme])

  // image gallery shuffle (robust)
  useEffect(() => {
    const gallery = document.querySelector(".image-gallery")
    if (!gallery) return
    const images = Array.from(gallery.querySelectorAll("img"))
    if (images.length === 0) return

    let idx = 0
    images.forEach((img, i) => {
      img.classList.remove("active")
      if (i === 0) img.classList.add("active")
    })

    const change = () => {
      images[idx].classList.remove("active")
      idx = (idx + 1) % images.length
      images[idx].classList.add("active")
    }
    const t = setInterval(change, 3000)
    return () => clearInterval(t)
  }, [])

  const scrollToLLM = () => document.querySelector(".llm")?.scrollIntoView({ behavior: "smooth" })

  return (
    <>
      <div className="hero">
        <div className="left-panel">
          <div className="hero-content">
            <h1>SMRZ 10K Report</h1>
            <p>
              Choose from the two most powerful, lightweight and open-source
              LLMs to summarize your SEC Report. Fast, secure and intelligent.
            </p>
            <div className="buttons-group theme-buttons">
              <button className="scroll-down-inline" onClick={scrollToLLM}>
                <svg viewBox="0 0 24 24" width="18" height="18">
                  <path fill="currentColor" d="M12 15.6L5.6 9.2 7 7.8 12 12.8 17 7.8 18.4 9.2z" />
                </svg>
              </button>
              <button className={`theme-button light-theme ${theme === "light-theme" ? "active" : ""}`} onClick={() => setTheme("light-theme")}>
                Light
              </button>
              <button className={`theme-button paper-theme ${theme === "paper-theme" ? "active" : ""}`} onClick={() => setTheme("paper-theme")}>
                Paper
              </button>
              <button className={`theme-button dark-theme ${theme === "dark-theme" ? "active" : ""}`} onClick={() => setTheme("dark-theme")}>
                Dark
              </button>
            </div>
          </div>
        </div>
        <div className="right-panel" aria-hidden="true">
          <div className="image-gallery">
            <img src="/image1.jpg" alt="gallery1" className="active" />
            <img src="/image2.jpg" alt="gallery2" />
            <img src="/image3.jpg" alt="gallery3" />
            <img src="/image4.jpg" alt="gallery4" />
          </div>
        </div>
      </div>

      <div className="llm">
        <div className="llm-container">
          <div className="llm-cards">
            <LLMCard title="Llama 3.1" author="Meta Inc." extraClass="llama" theme={theme} />
            <LLMCard title="Mistral-Nemo" author="Mistral AI & Nvidia" extraClass="mistral" theme={theme} />
          </div>
        </div>
      </div>

      <div className="footer">
        <div>
          <p>
            Liked my work?{" "}
            <a href="https://www.linkedin.com/in/aditya-nair-24a096214/" target="_blank" rel="noreferrer">
              Connect
            </a>{" "}
            🤝
          </p>
        </div>
        <div>
          <p>
            Made with ❤️ in India{" "}
            <img src="https://www.svgrepo.com/show/405510/flag-for-flag-india.svg" alt="India flag" className="icon-inline" />
          </p>
        </div>
        <div>
          <p>
            <img src="https://www.svgrepo.com/show/533405/badge-check.svg" alt="verified" className="icon-inline" /> Built with ChatGPT and Ollama
          </p>
        </div>
      </div>
    </>
  )
}
