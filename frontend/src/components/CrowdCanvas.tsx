import { useEffect, useRef } from 'react'
import gsap from 'gsap'
import './CrowdCanvas.css'

interface CrowdCanvasProps {
  src?: string
  rows?: number
  cols?: number
  speedMultiplier?: number
  className?: string
}

class Peep {
  image: HTMLImageElement
  rect: number[]
  width: number
  height: number
  drawArgs: any[]
  x: number = 0
  y: number = 0
  anchorY: number = 0
  scaleX: number = 1
  walk: gsap.core.Timeline | null = null

  constructor({ image, rect }: { image: HTMLImageElement; rect: number[] }) {
    this.image = image
    this.rect = rect
    this.width = rect[2]
    this.height = rect[3]
    this.drawArgs = [this.image, ...rect, 0, 0, this.width, this.height]
  }

  render(ctx: CanvasRenderingContext2D) {
    ctx.save()
    ctx.translate(this.x, this.y)
    ctx.scale(this.scaleX, 1)
    ctx.drawImage(...this.drawArgs)
    ctx.restore()
  }
}

const randomRange = (min: number, max: number) => min + Math.random() * (max - min)
const randomIndex = (array: any[]) => (randomRange(0, array.length) | 0)
const removeFromArray = (array: any[], i: number) => array.splice(i, 1)[0]
const removeItemFromArray = (array: any[], item: any) => removeFromArray(array, array.indexOf(item))
const removeRandomFromArray = (array: any[]) => removeFromArray(array, randomIndex(array))
const getRandomFromArray = (array: any[]) => array[randomIndex(array) | 0]

export function CrowdCanvas({ 
  src = 'https://s3-us-west-2.amazonaws.com/s.cdpn.io/175711/open-peeps-sheet.png',
  rows = 15,
  cols = 7,
  speedMultiplier = 1.8,
  className = '' 
}: CrowdCanvasProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)
  const stageRef = useRef({ width: 0, height: 0 })
  const allPeepsRef = useRef<Peep[]>([])
  const availablePeepsRef = useRef<Peep[]>([])
  const crowdRef = useRef<Peep[]>([])
  const tickerRef = useRef<(() => void) | null>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const container = containerRef.current
    if (!canvas || !container) return

    const ctx = canvas.getContext('2d')
    if (!ctx) return

    const stage = stageRef.current
    const allPeeps = allPeepsRef.current
    const availablePeeps = availablePeepsRef.current
    const crowd = crowdRef.current

    // Load sprite sheet
    const img = new Image()
    img.crossOrigin = 'anonymous'
    
    img.onload = () => {
      // Create all peep sprites from the sheet
      const { naturalWidth: width, naturalHeight: height } = img
      const total = rows * cols
      const rectWidth = width / rows
      const rectHeight = height / cols

      allPeeps.length = 0
      for (let i = 0; i < total; i++) {
        allPeeps.push(
          new Peep({
            image: img,
            rect: [
              (i % rows) * rectWidth,
              ((i / rows) | 0) * rectHeight,
              rectWidth,
              rectHeight,
            ],
          })
        )
      }

      resize()
      initCrowd()

      // Setup render loop with GSAP ticker
      const render = () => {
        canvas.width = canvas.width // Clear canvas
        ctx.save()
        ctx.scale(devicePixelRatio, devicePixelRatio)
        crowd.forEach((peep) => peep.render(ctx))
        ctx.restore()
      }

      tickerRef.current = render
      gsap.ticker.add(render)
    }

    img.src = src

    // Utility functions
    const resetPeep = (peep: Peep) => {
      const direction = Math.random() > 0.5 ? 1 : -1
      const offsetY = 50 - 250 * (gsap.parseEase('power2.in')(Math.random()) as number)
      // Shift the entire crowd down by 60px so the tallest characters'
      // heads clear the top edge of the canvas with breathing room.
      const downwardShift = 60
      const startY = stage.height - peep.height + offsetY + downwardShift
      let startX: number
      let endX: number

      if (direction === 1) {
        startX = -peep.width
        endX = stage.width
        peep.scaleX = 1
      } else {
        startX = stage.width + peep.width
        endX = 0
        peep.scaleX = -1
      }

      peep.x = startX
      peep.y = startY
      peep.anchorY = startY

      return { startX, startY, endX }
    }

    const normalWalk = (peep: Peep, props: { startX: number; startY: number; endX: number }) => {
      const { startY, endX } = props
      const xDuration = 10 / speedMultiplier // Faster walking
      const yDuration = 0.25 / speedMultiplier

      const tl = gsap.timeline()
      tl.timeScale(randomRange(0.8, 1.8)) // Increased speed variation
      tl.to(
        peep,
        {
          duration: xDuration,
          x: endX,
          ease: 'none',
        },
        0
      )
      tl.to(
        peep,
        {
          duration: yDuration,
          repeat: xDuration / yDuration,
          yoyo: true,
          y: startY - 10,
        },
        0
      )

      return tl
    }

    const addPeepToCrowd = () => {
      if (availablePeeps.length === 0) return null
      
      const peep = removeRandomFromArray(availablePeeps)
      const walk = normalWalk(peep, resetPeep(peep)).eventCallback('onComplete', () => {
        removePeepFromCrowd(peep)
        addPeepToCrowd()
      })

      peep.walk = walk
      crowd.push(peep)
      crowd.sort((a, b) => a.anchorY - b.anchorY)

      return peep
    }

    const removePeepFromCrowd = (peep: Peep) => {
      removeItemFromArray(crowd, peep)
      availablePeeps.push(peep)
    }

    const initCrowd = () => {
      while (availablePeeps.length) {
        const peep = addPeepToCrowd()
        if (peep && peep.walk) {
          peep.walk.progress(Math.random())
        }
      }
    }

    const resize = () => {
      stage.width = canvas.clientWidth
      stage.height = canvas.clientHeight
      canvas.width = stage.width * devicePixelRatio
      canvas.height = stage.height * devicePixelRatio

      crowd.forEach((peep) => {
        if (peep.walk) peep.walk.kill()
      })

      crowd.length = 0
      availablePeeps.length = 0
      availablePeeps.push(...allPeeps)

      if (allPeeps.length > 0) {
        initCrowd()
      }
    }

    window.addEventListener('resize', resize)

    return () => {
      window.removeEventListener('resize', resize)
      if (tickerRef.current) {
        gsap.ticker.remove(tickerRef.current)
      }
      crowd.forEach((peep) => {
        if (peep.walk) peep.walk.kill()
      })
    }
  }, [src, rows, cols, speedMultiplier])

  return (
    <div ref={containerRef} className={`crowd-canvas-container ${className}`}>
      <canvas ref={canvasRef} className="crowd-canvas" />
    </div>
  )
}
