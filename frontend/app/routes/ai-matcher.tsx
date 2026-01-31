import React, { useEffect, useMemo, useRef, useState } from "react";
import HomeCard, { type Home } from "../components/HomeCard";
import useHomes from "../hooks/useHomes";

function clamp(v: number, a = -1, b = 1) {
  return Math.max(a, Math.min(b, v));
}

export default function AIMatcher() {
  const { homes, loading } = useHomes();
  const [cards, setCards] = useState<Home[]>([]);

  useEffect(() => {
    setCards(homes ?? []);
  }, [homes]);

  const topIndex = cards.length - 1;

  // gesture state
  const [dragging, setDragging] = useState(false);
  const startRef = useRef<{ x: number; y: number } | null>(null);
  const [tx, setTx] = useState(0);
  const [ty, setTy] = useState(0);
  const [rot, setRot] = useState(0);
  const [isAnimatingOut, setIsAnimatingOut] = useState(false);

  useEffect(() => {
    if (!dragging && !isAnimatingOut) {
      setTx(0);
      setTy(0);
      setRot(0);
    }
  }, [dragging, isAnimatingOut]);

  useEffect(() => {
    // reset animation flag when cards change
    setIsAnimatingOut(false);
  }, [cards.length]);

  const handlePointerDown = (e: React.PointerEvent) => {
    (e.target as Element).setPointerCapture(e.pointerId);
    startRef.current = { x: e.clientX, y: e.clientY };
    setDragging(true);
    setIsAnimatingOut(false);
  };

  const handlePointerMove = (e: React.PointerEvent) => {
    if (!dragging || !startRef.current) return;
    const dx = e.clientX - startRef.current.x;
    const dy = e.clientY - startRef.current.y;
    setTx(dx);
    setTy(dy);
    // rotation proportional to horizontal drag
    setRot(clamp(dx / 20, -25, 25));
  };

  const commitSwipe = (direction: "left" | "right") => {
    const home = cards[topIndex];
    if (!home) return;

    // Log the property's stats on swipe
    console.log(direction === "right" ? "LIKE" : "DISLIKE", {
      id: home.id,
      title: home.title,
      location: home.location,
      price: home.price,
      beds: home.beds,
      baths: home.baths,
      amenities: home.amenities,
    });

    // animate out then remove
    setIsAnimatingOut(true);
    const outX = direction === "right" ? window.innerWidth : -window.innerWidth;
    setTx(outX);
    setRot(direction === "right" ? 30 : -30);

    setTimeout(() => {
      setCards((prev) => prev.slice(0, Math.max(0, prev.length - 1)));
      // reset
      setTx(0);
      setTy(0);
      setRot(0);
      setIsAnimatingOut(false);
    }, 300);
  };

  const handlePointerUp = (e: React.PointerEvent) => {
    if (!startRef.current) return;
    (e.target as Element).releasePointerCapture?.(e.pointerId);
    setDragging(false);
    const dx = tx;
    const threshold = 120;
    if (Math.abs(dx) > threshold) {
      commitSwipe(dx > 0 ? "right" : "left");
    } else {
      // snap back
      setTx(0);
      setTy(0);
      setRot(0);
    }
    startRef.current = null;
  };

  const handleButtonSwipe = (dir: "left" | "right") => () => commitSwipe(dir);

  const stack = useMemo(() => cards.slice(), [cards]);

  return (
    <div className="container mx-auto px-4 pt-6">
      <h2 className="text-2xl font-semibold mb-4">AI Matcher</h2>

      <div className="max-w-md mx-auto">
        <div className="relative h-[520px]">
          {loading && cards.length === 0 && (
            <div className="flex items-center justify-center h-full text-gray-500">Loading homes…</div>
          )}

          {stack.length === 0 && !loading && (
            <div className="flex items-center justify-center h-full text-gray-500">No more homes</div>
          )}

          {stack.map((home, idx) => {
            const indexFromTop = idx - topIndex; // top has 0
            const isTop = idx === topIndex;
            const offset = (topIndex - idx) * 8; // distance between stacked cards
            const scale = 1 - (topIndex - idx) * 0.02;

            const style: React.CSSProperties = isTop
              ? {
                  transform: `translate(${tx}px, ${ty}px) rotate(${rot}deg)`,
                  transition: dragging || isAnimatingOut ? "transform 0s" : "transform 200ms ease",
                  zIndex: 100 + idx,
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: `${offset}px`,
                }
              : {
                  transform: `scale(${scale})`,
                  transition: "transform 200ms ease",
                  zIndex: 50 + idx,
                  position: "absolute",
                  left: 0,
                  right: 0,
                  top: `${offset}px`,
                };

            return (
              <div
                key={String(home.id)}
                style={style}
                className="mx-auto w-full max-w-md cursor-grab"
                onPointerDown={isTop ? handlePointerDown : undefined}
                onPointerMove={isTop ? handlePointerMove : undefined}
                onPointerUp={isTop ? handlePointerUp : undefined}
                onPointerCancel={isTop ? handlePointerUp : undefined}
              >
                <HomeCard home={home} />
              </div>
            );
          })}
        </div>

        <div className="mt-6 flex items-center justify-center gap-6">
          <button
            onClick={handleButtonSwipe("left")}
            className="px-4 py-2 rounded-md bg-red-100 text-red-700 border border-red-200"
          >
            Dislike
          </button>
          <button
            onClick={handleButtonSwipe("right")}
            className="px-4 py-2 rounded-md bg-green-100 text-green-700 border border-green-200"
          >
            Like
          </button>
        </div>
      </div>
    </div>
  );
}
