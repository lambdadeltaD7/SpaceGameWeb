import {
    showToast,
    showErr,
    show_latest_transactions,
    base_url
} from "./utils.js"

const balance_info_txt = document.getElementById('balance_info_txt');

const user_to_id_input = document.getElementById('user_to_id_input');
const res1_input = document.getElementById('res1_input');
const res2_input = document.getElementById('res2_input');
const transaction_btn = document.getElementById('transaction_btn');

const reload_transactions_btn = document.getElementById('reload_transactions_btn');
const transactions_list = document.getElementById('transactions_list');


var user_id = null;


async function update_transactions() {
    const tr_r = await fetch(base_url + `/api/v1/transactions/?user_id=${user_id}`);
    const tr_d = await tr_r.json();

    transactions_list.innerHTML = '';

    for(const tr of tr_d){
        const el = document.createElement('p');
        el.className = 'transaction-card';
        el.textContent = JSON.stringify(tr, null, 2);
        transactions_list.append(el);
    }
}

async function init() {
    const result = await fetch(base_url + "/api/v1/auth/session_info");
    const session_info = await result.json();

    if(session_info.is_logged){
        user_id = session_info.user_id;

        const user_r = await fetch(base_url + `/api/v1/users/${user_id}`);
        const user_d = await user_r.json();

        balance_info_txt.textContent =
            'balance: (' +  
            `res1: ${session_info.res1}, ` +
            `res2: ${session_info.res2})`; 


        await update_transactions();

    }
    else{
        balance_info_txt.textContent = "no info about balance cuz yre not logged in";
    }
}


reload_transactions_btn.addEventListener('click', async () => {
    await init();
});

transaction_btn.addEventListener('click', async () => {

    const result = await fetch(
        base_url + `/api/v1/transactions/`,
        {
            method: 'POST',
            headers:{
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                'user_from_id': user_id,
                'user_to_id': user_to_id_input.value,
                'res1': res1_input.value,
                'res2': res2_input.value,
                'created_at': Math.round((performance.timeOrigin + performance.now()) / 1000) 
            })
        }
    )
});


queueMicrotask(async () => {await init();});

setInterval(async () => {await show_latest_transactions();}, 5000);
setInterval(async () => {await init();}, 5000);