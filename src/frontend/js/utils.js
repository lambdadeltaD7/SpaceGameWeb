export const base_url = "http://localhost:8004" 


export async function show_latest_transactions(){
    const result = await fetch(base_url + '/api/v1/transactions/latest_incoming');
    const data = await result.json();

    if(data.cnt != "0"){
        showToast(`you do have incoming transactions: \n ${JSON.stringify(data, null, 2)}`);
    }
}


export function showErr(txt){
    Swal.fire({
            icon: 'error',
            title: 'Input error',
            text: txt,
            });
}


export function showToast(txt){
    Swal.fire({
        toast: true,
        position: 'top-end',
        icon: 'success',
        title: txt,
        showConfirmButton: false,
        timer: 2000,
        timerProgressBar: true
        });
}


export function spreadImgOnBG(
    cnt = 50,
    img_path = '../img/star.png',
    scale = 20,
    offset = 4,
)
{
    const container = document.body;
    container.style.position = 'relative';

    for (let i = 0; i < cnt; i++) {
        const img_el = document.createElement('img');
        img_el.src = img_path;
        img_el.alt = '';
        img_el.style.position = 'absolute';
        img_el.style.width = `${Math.random() * scale + offset}px`;
        img_el.style.height = img_el.style.width;
        img_el.style.left = `${Math.random() * 100}%`;
        img_el.style.top = `${Math.random() * document.documentElement.scrollHeight}px`;
        img_el.style.pointerEvents = 'none';
        img_el.style.zIndex = '-1';
        img_el.style.userSelect = 'none';
        container.appendChild(img_el);
    }
}