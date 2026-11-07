const bar = document.getElementById('bar');
const close = document.getElementById('close');
const nav = document.getElementById('navbar');

if(bar){
    bar.addEventListener('click', ()=>{
        nav.classList.add('active');
    })
}

if(close){
    close.addEventListener('click', ()=>{
        nav.classList.remove('active');
    })
}



const slides = document.querySelectorAll('.slide');
const dots = document.querySelectorAll('.dot');
const prevBtn = document.querySelector('.prev-btn');
const nextBtn = document.querySelector('.next-btn');

let currentIdx = 0;

function updateCarouselState(index) {
    // Handle wrap-around bounds safely
    if (index >= slides.length) currentIdx = 0;
    else if (index < 0) currentIdx = slides.length - 1;
    else currentIdx = index;

    // Toggle active classes on slides
    slides.forEach((slide, idx) => {
        if (idx === currentIdx) {
            slide.classList.add('active');
        } else {
            slide.classList.remove('active');
        }
    });

    // Toggle active state on bottom indicators
    dots.forEach((dot, idx) => {
        if (idx === currentIdx) {
            dot.classList.add('active');
        } else {
            dot.classList.remove('active');
        }
    });
}

// Arrow Button Listeners
nextBtn.addEventListener('click', () => updateCarouselState(currentIdx + 1));
prevBtn.addEventListener('click', () => updateCarouselState(currentIdx - 1));

// Bottom Dot Indicator Listeners
dots.forEach((dot, index) => {
    dot.addEventListener('click', () => updateCarouselState(index));
});

// Optional: Enable auto-play behavior cycling every 5 seconds
let autoCycle = setInterval(() => updateCarouselState(currentIdx + 1), 5000);

// Reset auto-play timer when user interacts directly
function resetTimer() {
    clearInterval(autoCycle);
    autoCycle = setInterval(() => updateCarouselState(currentIdx + 1), 5000);
}

[nextBtn, prevBtn, ...dots].forEach(element => {
    element.addEventListener('click', resetTimer);
});

