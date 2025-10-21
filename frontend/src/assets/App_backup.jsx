import { useEffect, useState } from "react"
import "./index.css"

// Color matrix for Mistral-Nemo backlayer (6 rows × 8 cols)
const mistralColors = [
  ["#FFF0C2","#FFF0C2","#FFF0C2","#333333","#333333","#76B900","#76B900","#76B900"],
  ["#FFD900","#FFD900","#333333","#333333","#333333","#333333","#5FA800","#5FA800"],
  ["#FFAE00","#333333","#333333","#333333","#333333","#333333","#333333","#489701"],
  ["#FF8205","#333333","#333333","#333333","#333333","#333333","#333333","#318501"],
  ["#FA520F","#FA520F","#333333","#333333","#333333","#333333","#1A7402","#1A7402"],
  ["#E00400","#E00400","#E00400","#333333","#333333","#036302","#036302","#036302"],
]

function LLMCard({ title, author, extraClass = "" }) {
  const [step, setStep] = useState("front")
  const [file, setFile] = useState(null)
  const [progress, setProgress] = useState(0)

  useEffect(() => {
    if (step === "progress") {
      let value = 0
      const interval = setInterval(() => {
        value += 10
        setProgress(value)
        if (value >= 100) {
          clearInterval(interval)
          setStep("download")
        }
      }, 300)
      return () => clearInterval(interval)
    }
  }, [step])

  const handleFileUpload = (e) => {
    const uploadedFile = e.target.files[0]
    if (uploadedFile) {
      setFile(uploadedFile)
      setStep("progress")
    }
  }

  const resetCard = () => {
    setStep("front")
    setFile(null)
    setProgress(0)
  }

  return (
    <div
      className={`llm-card ${extraClass}`}
      onMouseMove={(e) => {
        if (extraClass !== "mistral") return

        const rect = e.currentTarget.getBoundingClientRect()
        const x = e.clientX - rect.left
        const y = e.clientY - rect.top

        e.currentTarget.style.setProperty("--x", `${x}px`)
        e.currentTarget.style.setProperty("--y", `${y}px`)
      }}
      onMouseLeave={(e) => {
        if (extraClass !== "mistral") return
        e.currentTarget.style.removeProperty("--x")
        e.currentTarget.style.removeProperty("--y")
      }}
    >
      {/* BACKLAYER for Mistral-Nemo */}
      {extraClass === "mistral" && (
        <div className="mistral-grid">
          {mistralColors.map((row, rIdx) =>
            row.map((color, cIdx) => (
              <div
                key={`${rIdx}-${cIdx}`}
                className="grid-cell"
                style={{ "--cell-color": color }}
              ></div>
            ))
          )}
        </div>
      )}

      {/* FORELAYER CONTENT */}
      {step === "front" && (
        <div className="card-face card-front">
          <h2>{title}</h2>
          <h5>by</h5>
          <h4>{author}</h4>
          <button className="upload-btn" onClick={() => setStep("upload")}>
            Start
          </button>
        </div>
      )}

      {step === "upload" && (
        <div className="card-face card-back upload-section">
          <input
            type="file"
            accept=".pdf"
            style={{ display: "none" }}
            id={`${title}-file`}
            onChange={handleFileUpload}
          />
          <label htmlFor={`${title}-file`} className="upload-btn">
            Upload PDF
          </label>
          <button className="go-back-btn" onClick={resetCard}>
            ⬅ Back
          </button>
        </div>
      )}

      {step === "progress" && (
        <div className="card-face card-back download-section">
          <div className="progress-container">
            <div className="progress-bar" style={{ width: `${progress}%` }}></div>
          </div>
          <p>Processing {file?.name}...</p>
        </div>
      )}

      {step === "download" && (
        <div className="card-face card-back download-section">
          <button className="download-btn">Download Result</button>
          <p>{file?.name.replace(".pdf", "_summary.pdf")}</p>
          <button className="go-back-btn" onClick={resetCard}>
            ⬅ Reset
          </button>
        </div>
      )}
    </div>
  )
}

export default function App() {
  // image gallery, theme, scroll logic remain unchanged
  useEffect(() => {
    const images = document.querySelectorAll(".image-gallery img")
    let currentIndex = 0
    if (images.length > 0) {
      images[0].classList.add("active")
      const changeImage = () => {
        images[currentIndex].classList.remove("active")
        currentIndex = (currentIndex + 1) % images.length
        images[currentIndex].classList.add("active")
      }
      const interval = setInterval(changeImage, 3000)
      return () => clearInterval(interval)
    }
  }, [])

  const [theme, setTheme] = useState("light-theme")
  useEffect(() => {
    document.body.classList.remove("light-theme", "dark-theme", "paper-theme")
    document.body.classList.add(theme)
  }, [theme])

  const scrollToLLM = () => {
    const llmSection = document.querySelector(".llm")
    if (llmSection) {
      llmSection.scrollIntoView({ behavior: "smooth", block: "start" })
    }
  }

  return (
    <>
      {/* HERO */}
      <div className="hero">
        <div className="left-panel">
          <div className="hero-content">
            <h1>SMRZ 10K Report</h1>
            <p>
              Choose from the two most powerful, lightweight and open-source LLMs to
              summarize your SEC Report. Fast, secure and intelligent.
            </p>
            <div className="buttons-group theme-buttons">
              <button className="scroll-down-inline" onClick={scrollToLLM}>
                <svg viewBox="0 0 24 24" width="18" height="18">
                  <path
                    fill="currentColor"
                    d="M12 15.6L5.6 9.2 7 7.8 12 12.8 17 7.8 18.4 9.2z"
                  />
                </svg>
              </button>
              <button
                className={`theme-button light-theme ${theme === "light-theme" ? "active" : ""}`}
                onClick={() => setTheme("light-theme")}
              >
                Light
              </button>
              <button
                className={`theme-button paper-theme ${theme === "paper-theme" ? "active" : ""}`}
                onClick={() => setTheme("paper-theme")}
              >
                Paper
              </button>
              <button
                className={`theme-button dark-theme ${theme === "dark-theme" ? "active" : ""}`}
                onClick={() => setTheme("dark-theme")}
              >
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

      {/* LLM CARDS */}
      <div className="llm">
        <div className="llm-container">
          <div className="llm-cards">
            <LLMCard title="Llama 3.1" author="Meta Inc." extraClass="llama" />
            <LLMCard title="Mistral-Nemo" author="Mistral AI & NVIDIA" extraClass="mistral" />
          </div>
        </div>
      </div>

      {/* FOOTER */}
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
            <img src="https://www.svgrepo.com/show/533405/badge-check.svg" alt="verified" className="icon-inline" /> Built with ChatGPT, Llama and Mistral
          </p>
        </div>
      </div>
    </>
  )
}
