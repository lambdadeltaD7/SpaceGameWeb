import {
    showToast,
    showErr,
    show_latest_transactions,
    base_url
} from "./utils.js"

const username_input = document.getElementById('username_input');
const password_input = document.getElementById('password_input');
const email_input = document.getElementById('email_input');
const register_btn = document.getElementById('register_btn');
const status_text = document.getElementById('status_text');




async function init(){
    const result = await fetch(base_url + "/api/v1/auth/session_info");
    const data = await result.json();

    if(data.is_logged){
        window.location.href = base_url;
    }
}

async function try_register(params){

    const user_obj = {
        "user_name" : username_input.value,
        "user_email" : email_input.value,
        "user_password" : password_input.value
    }; 

    const result = await fetch(
        base_url + `/api/v1/auth/registration`,
        {
            method: 'POST',

            headers: {
                'Content-Type': 'application/json',
            },

            body: JSON.stringify(user_obj)
        }
    );

    if(!result.ok){
        status_text.textContent = "something went wrong";
        setTimeout(()=>{status_text.textContent = "";}, 3000);
    }
    else{
        window.location.href = base_url;
    }

}

register_btn.addEventListener('click', async () => {await try_register();});

document.addEventListener('keydown', async function(event){
    if(event.key == "Enter"){
        await try_register();
    }
    if(event.key == "Escape"){
        username_input.value = "";
        password_input.value = "";
        email_input.value = "";
    }
});

queueMicrotask(async () => {await init();});

setInterval(async () => {await show_latest_transactions();}, 5000);