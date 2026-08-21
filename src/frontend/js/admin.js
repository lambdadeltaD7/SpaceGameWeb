import {
    showToast,
    showErr,
    show_latest_transactions,
    base_url
} from "./utils.js"

const sessions_list = document.getElementById('sessions_list');
const users_list = document.getElementById('users_list');
const transactions_list = document.getElementById('transactions_list');



function clear_all(){
    sessions_list.innerHTML = '';
    users_list.innerHTML = '';
    transactions_list.innerHTML = '';
}


async function refresh_sessions(){

    const sessions_result = await fetch(base_url + "/api/v1/admin/sessions");
    const sessions_data = await sessions_result.json();

    sessions_list.innerHTML = '';

    const hdr_el = document.createElement("h2");
    hdr_el.textContent = "Sessions:"
    sessions_list.append(hdr_el);

    const refresh_btn = document.createElement('button');
    refresh_btn.type = 'button';
    refresh_btn.className = 'admin-btn';
    refresh_btn.addEventListener('click', async () => {await refresh_sessions();});
    refresh_btn.textContent = "refresh sessions";
    sessions_list.append(refresh_btn);

    for(const ses of sessions_data){
        const ses_card = document.createElement('div')
        ses_card.className = 'admin-item';

        const ses_info = document.createElement('p');
        ses_info.className = 'admin-item-info';
        ses_info.textContent = JSON.stringify(ses, null, 2);
        ses_card.append(ses_info);

        const kill_btn = document.createElement('button');
        kill_btn.type = 'button';
        kill_btn.className = 'admin-btn';
        kill_btn.textContent = "kill session";
        kill_btn.addEventListener('click', async () => {
            await fetch(
                base_url + `/api/v1/admin/kill_session?session_id=${ses.session_id}`,
                {
                    method: 'DELETE'
                }
            );
            await refresh_sessions();
        });

        const btn_container = document.createElement('div');
        btn_container.className = 'button-container';
        btn_container.append(kill_btn);
        ses_card.append(btn_container);

        sessions_list.append(ses_card);
    }

}


async function refresh_users(){

    const users_result = await fetch(base_url + "/api/v1/users/");
    const users_data = await users_result.json();

    users_list.innerHTML = '';

    const hdr_el = document.createElement("h2");
    hdr_el.textContent = "Users:"
    users_list.append(hdr_el);

    const refresh_btn = document.createElement('button');
    refresh_btn.type = 'button';
    refresh_btn.className = 'admin-btn';
    refresh_btn.addEventListener('click', async () => {await refresh_users();});
    refresh_btn.textContent = "refresh users";
    users_list.append(refresh_btn);

    for(const usr of users_data){
        const usr_card = document.createElement('div')
        usr_card.className = 'admin-item';

        const usr_info = document.createElement('p');
        usr_info.className = 'admin-item-info';
        usr_info.textContent = JSON.stringify(usr, null, 2);
        usr_card.append(usr_info);

        const kill_btn = document.createElement('button');
        kill_btn.type = 'button';
        kill_btn.className = 'admin-btn';
        kill_btn.textContent = "delete user";
        kill_btn.addEventListener('click', async () => {
            await fetch(
                base_url + `/api/v1/users/${usr.user_id}`,
                {
                    method: 'DELETE'
                }
            );
            await refresh_users();
        });

        const change_is_admin_btn = document.createElement('button');
        change_is_admin_btn.type = 'button';
        change_is_admin_btn.className = 'admin-btn';
        change_is_admin_btn.textContent = "change is_admin";
        change_is_admin_btn.addEventListener('click', async () => {
            await fetch(
                base_url + `/api/v1/users/${usr.user_id}?is_admin=${!usr.is_admin}`,
                {
                    method: 'PATCH'
                }
            );
            await refresh_users();
            await refresh_sessions();
        });

        const btn_container = document.createElement('div');
        btn_container.className = 'button-container';
        btn_container.append(kill_btn, change_is_admin_btn);
        usr_card.append(btn_container);

        users_list.append(usr_card);
    }
    
}


async function refresh_transactions(){

    const transactions_result = await fetch(base_url + "/api/v1/transactions/");
    const transactions_data = await transactions_result.json();

    transactions_list.innerHTML = '';

    const hdr_el = document.createElement("h2");
    hdr_el.textContent = "Transactions:"
    transactions_list.append(hdr_el);

    const refresh_btn = document.createElement('button');
    refresh_btn.type = 'button';
    refresh_btn.className = 'admin-btn';
    refresh_btn.addEventListener('click', async () => {await refresh_transactions();});
    refresh_btn.textContent = "refresh transactions";
    transactions_list.append(refresh_btn);

    for(const trans of transactions_data){
        const trans_card = document.createElement('div')
        trans_card.className = 'admin-item';

        const trans_info = document.createElement('p');
        trans_info.className = 'admin-item-info';
        trans_info.textContent = JSON.stringify(trans, null, 2);
        trans_card.append(trans_info);

        const kill_btn = document.createElement('button');
        kill_btn.type = 'button';
        kill_btn.className = 'admin-btn';
        kill_btn.textContent = "undo transaction";
        kill_btn.addEventListener('click', async () => {
            await fetch(
                base_url + `/api/v1/transactions/${trans.transaction_id}`,
                {
                    method: 'DELETE'
                }
            );
            await refresh_transactions();
        });

        const btn_container = document.createElement('div');
        btn_container.className = 'button-container';
        btn_container.append(kill_btn);
        trans_card.append(btn_container);

        transactions_list.append(trans_card);
    }
    
}


async function refresh_all() {
    await refresh_users();
    await refresh_sessions();
    await refresh_transactions();
}


async function init() {
    const result = await fetch(base_url + "/api/v1/auth/session_info");
    const data = await result.json();
    
    if(data.is_logged && (data.is_admin=="1")){
        await refresh_all();
    }
    else{
        alert("only for admins");
    }

}


queueMicrotask(async () => {await init();});

setInterval(async () => {await show_latest_transactions();}, 5000);