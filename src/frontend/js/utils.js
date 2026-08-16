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
