<script setup>
// Decorative shipyard at dawn behind the auth forms: original artwork, no external assets. Hidden from assistive tech.
const range = (n, from, step) => Array.from({ length: n }, (_, i) => from + i * step)
const girderBays = range(19, 684, 45)
const hullSeams = range(8, 250, 90)
const hatches = range(4, 250, 108)
const stations = range(8, 205, 96)
const windows = range(7, 732, 15)
const towers = [{ x: 96, h: 300, jib: 190 }, { x: 1540, h: 250, jib: -150 }]
</script>

<template>
  <svg class="auth-scene" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMax slice" aria-hidden="true" focusable="false">
    <defs>
      <linearGradient id="as-sky" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#060f22" /><stop offset=".55" stop-color="#0c2344" />
        <stop offset=".78" stop-color="#1b4470" /><stop offset=".85" stop-color="#3a6187" />
      </linearGradient>
      <radialGradient id="as-glow" cx="50%" cy="100%" r="70%">
        <stop offset="0" stop-color="#f6a65a" stop-opacity=".55" /><stop offset=".45" stop-color="#e0815a" stop-opacity=".16" />
        <stop offset="1" stop-color="#e0815a" stop-opacity="0" />
      </radialGradient>
      <linearGradient id="as-hull" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#1c3f6e" /><stop offset=".72" stop-color="#0f2547" /><stop offset=".73" stop-color="#6d2a2f" /><stop offset="1" stop-color="#3f1a24" />
      </linearGradient>
      <linearGradient id="as-water" x1="0" y1="0" x2="0" y2="1">
        <stop offset="0" stop-color="#17395f" /><stop offset="1" stop-color="#050d1d" />
      </linearGradient>
      <linearGradient id="as-fade" x1="0" y1="0" x2="1" y2="1">
        <stop offset="0" stop-color="#fff" stop-opacity=".9" /><stop offset=".6" stop-color="#fff" stop-opacity=".12" /><stop offset="1" stop-color="#fff" stop-opacity="0" />
      </linearGradient>
      <mask id="as-gridmask"><rect width="1600" height="900" fill="url(#as-fade)" /></mask>
      <pattern id="as-grid" width="40" height="40" patternUnits="userSpaceOnUse">
        <path d="M40 0H0V40" fill="none" stroke="#7fb4e8" stroke-opacity=".16" />
      </pattern>
      <pattern id="as-grid5" width="200" height="200" patternUnits="userSpaceOnUse">
        <path d="M200 0H0V200" fill="none" stroke="#7fb4e8" stroke-opacity=".22" />
      </pattern>
      <path id="as-hullshape" d="M150 632 L900 640 L918 700 L885 760 H262 Q212 706 150 632 Z" />
    </defs>

    <rect width="1600" height="900" fill="url(#as-sky)" />
    <rect x="300" y="380" width="1300" height="385" fill="url(#as-glow)" />
    <g mask="url(#as-gridmask)"><rect width="1600" height="900" fill="url(#as-grid)" /><rect width="1600" height="900" fill="url(#as-grid5)" /></g>

    <!-- far shore -->
    <path d="M0 738 H90 V716 H150 V728 H260 V706 H330 V730 H470 V722 H600 V738 H1600 V766 H0 Z" fill="#0d2746" />

    <!-- tower cranes -->
    <g v-for="t in towers" :key="t.x" stroke="#17365f" fill="none">
      <path :d="`M${t.x} 740 V${740 - t.h}`" stroke-width="10" />
      <path :d="`M${t.x - t.jib * .28} ${740 - t.h} H${t.x + t.jib}`" stroke-width="5" />
      <path :d="`M${t.x} ${716 - t.h} L${t.x + t.jib * .85} ${740 - t.h} M${t.x} ${716 - t.h} L${t.x - t.jib * .28} ${740 - t.h}`" stroke-width="1.5" />
      <path :d="`M${t.x + t.jib * .62} ${740 - t.h} v90`" stroke-width="1.5" />
    </g>

    <!-- goliath crane -->
    <g class="goliath">
      <path d="M716 752 L772 292 L806 292 L780 752 Z M1486 752 L1456 292 L1490 292 L1548 752 Z" fill="#14305a" />
      <path d="M736 752 L786 292 M1520 752 L1472 292" stroke="#2c5587" stroke-width="1.5" />
      <path d="M744 560 H786 M1484 560 H1526" stroke="#2c5587" stroke-width="5" />
      <rect x="684" y="236" width="860" height="10" fill="#2a5286" />
      <rect x="684" y="282" width="860" height="10" fill="#17365f" />
      <path v-for="x in girderBays" :key="x" :d="`M${x} 282 L${x + 22} 246 L${x + 45} 282`" fill="none" stroke="#1f4372" stroke-width="3" />
      <g class="trolley">
        <rect x="1000" y="214" width="96" height="24" rx="2" fill="#d97f2a" />
        <rect x="1012" y="292" width="72" height="12" fill="#2a5286" />
        <path d="M1030 304 V470 M1066 304 V470" stroke="#6f93bb" stroke-width="1.5" />
        <rect x="984" y="470" width="128" height="74" fill="#16325a" stroke="#4a7cb3" />
        <path d="M984 498 H1112 M1020 470 V544 M1076 470 V544" stroke="#4a7cb3" stroke-opacity=".6" />
      </g>
      <circle class="beacon" cx="690" cy="228" r="4" fill="#ff5a4d" />
      <circle class="beacon late" cx="1538" cy="228" r="4" fill="#ff5a4d" />
    </g>

    <!-- ship under construction, bow to the left -->
    <use href="#as-hullshape" fill="url(#as-hull)" />
    <path d="M150 632 L900 640" stroke="#8cc1f2" stroke-opacity=".8" stroke-width="1.5" fill="none" />
    <g stroke="#a9cdf0" stroke-opacity=".13">
      <path v-for="x in hullSeams" :key="x" :d="`M${x} 636 V760`" />
      <path d="M182 672 H910 M214 708 H908" />
    </g>
    <g fill="#163760" stroke="#3d6da3">
      <rect v-for="x in hatches" :key="x" :x="x" y="616" width="112" height="19" rx="1" />
    </g>
    <g fill="#d8e2ee">
      <rect x="716" y="568" width="164" height="70" fill="#a7b7ca" />
      <rect x="728" y="528" width="130" height="40" fill="#c2cedc" />
      <rect x="716" y="500" width="150" height="28" fill="#dbe4ee" />
      <rect x="836" y="462" width="36" height="76" fill="#c9752b" />
      <rect x="834" y="456" width="40" height="8" fill="#26303d" />
    </g>
    <g fill="#ffd28a">
      <rect v-for="x in windows" :key="x" :x="x" y="509" width="9" height="6" />
      <rect v-for="x in windows" :key="'b' + x" :x="x + 2" y="542" width="8" height="5" opacity=".7" />
      <rect v-for="x in windows" :key="'c' + x" :x="x" y="592" width="8" height="5" opacity=".5" />
    </g>

    <!-- drawing marks: the ship as a blueprint -->
    <g class="marks" stroke="#8cc1f2" fill="none">
      <path d="M150 596 V622 M918 596 V690 M150 602 H700" stroke-opacity=".55" />
      <path d="M150 602 l10 -3 v6 z" fill="#8cc1f2" stroke="none" />
      <path v-for="x in stations" :key="x" :d="`M${x} 598 v8`" stroke-opacity=".5" />
      <path d="M100 760 H980" stroke-dasharray="14 5 3 5" stroke-opacity=".45" />
    </g>

    <!-- water -->
    <rect y="760" width="1600" height="140" fill="url(#as-water)" />
    <use href="#as-hullshape" transform="matrix(1 0 0 -.62 0 1231)" fill="#0a1a33" opacity=".55" />
    <g stroke="#f6c690" stroke-linecap="round">
      <path d="M820 776 H1180 M900 792 H1120 M960 812 H1080" stroke-opacity=".3" />
    </g>
    <g stroke="#8cc1f2" stroke-linecap="round" stroke-opacity=".16">
      <path d="M120 784 H420 M260 812 H640 M1220 786 H1520 M1100 838 H1460 M60 852 H360" />
    </g>
  </svg>
</template>

<style scoped>
.auth-scene { position:absolute; inset:0; width:100%; height:100%; pointer-events:none; }
.trolley { animation:as-travel 26s ease-in-out infinite alternate; }
.beacon { animation:as-blink 2.8s ease-in-out infinite; } .beacon.late { animation-delay:1.4s; }
@keyframes as-travel { from { transform:translateX(-30px); } to { transform:translateX(190px); } }
@keyframes as-blink { 0%, 100% { opacity:.25; } 50% { opacity:1; } }
@media (prefers-reduced-motion:reduce) { .trolley, .beacon { animation:none; } }
</style>
