window.addEventListener('DOMContentLoaded', () => { 
    
    let editBtn = document.querySelectorAll('.edit'),
        divPhoto = document.querySelector('.photo'),
        titlePost = document.querySelector('.title'),
        descriptionPost = document.querySelector('.description');


    divPhoto.addEventListener('click', (event) => {
        if (event.target && event.target.classList.contains('photo') == 'edit') {
            console.log('LOL!');
        }
    });


  });