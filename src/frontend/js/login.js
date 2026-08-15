const username_input = document.getElementById('username_input');
const password_input = document.getElementById('password_input');
const login_btn = document.getElementById('login_btn');
const register_btn = document.getElementById('register_btn');
const status_text = document.getElementById('status_text');


const base_url = "http://localhost:8004" 


async function init(){
    const result = await fetch(base_url + "/api/v1/auth/session_info");
    const data = await result.json();

    if(data.is_logged){
        window.location.href = base_url;
    }
}


login_btn.addEventListener('click', async () => {

    console.log("click");

    const user_obj = {
        "user_name" : username_input.value,
        "user_password" : password_input.value
    }; 

    const result = await fetch(
        base_url + '/api/v1/auth/login',
        {
            method: 'POST',

            headers: {
                'Content-Type': 'application/json',
            },
            
            body: JSON.stringify(user_obj)
        }
    );
    

    if(!result.ok || result.status==401){
        status_text.textContent = "bad credentials";
        setTimeout(()=>{status_text.textContent = "";}, 3000);
    }
    else{
        window.location.href = base_url;
    }

});


register_btn.addEventListener('click', async () => {
    window.location.href = base_url + "/registration";
});


queueMicrotask(async () => {await init();});