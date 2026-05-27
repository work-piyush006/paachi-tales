const toggle = document.querySelector('.nav-toggle');
const links = document.querySelector('.nav-links');
if (toggle && links) toggle.addEventListener('click', () => links.classList.toggle('open'));

document.querySelectorAll('img[loading="lazy"]').forEach((img) => {
  img.addEventListener('error', () => img.style.opacity = '.4');
});
