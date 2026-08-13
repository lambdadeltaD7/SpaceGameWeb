const base_url = "http://localhost:8004" 

const login_button = document.getElementById('login_button');
const register_button = document.getElementById('register_button');
const logout_button = document.getElementById('logout_button');
const worlds_btn = document.getElementById('worlds_btn');
const status_text = document.getElementById('status_text');
const online_info_text = document.getElementById('online_info_text');

async function init(){
    const result = await fetch(base_url + "/api/v1/auth/session_info");
    const data = await result.json();

    status_text.textContent = data.msg;   

    if(data.is_logged){
        login_button.style.display = "none";
        register_button.style.display = "none";
        logout_button.style.display = "block";
    }
    else{
        login_button.style.display = "block";
        register_button.style.display = "block";
        logout_button.style.display = "none";
    }

}


async function update_online_info(){
    const result = await fetch(base_url + "/api/v1/auth/online_info");
    const data = await result.json();
    online_info_text.textContent = `users_online: ${data.online_cnt} | users_logged: ${data.logged_cnt}`;
}

login_button.addEventListener('click', async () => {
    window.location.href = base_url + "/login";
});

register_button.addEventListener('click', async () => {
    window.location.href = base_url + "/registration";
});

logout_button.addEventListener('click', async () => {
    await fetch(base_url + "/api/v1/auth/logout");
    await init();
});

worlds_btn.addEventListener('click', async () => {
    window.location.href = base_url + "/worlds";
});

init();
update_online_info();
setInterval(update_online_info, 3000);