const btnelement = document.getElementById("submit");
const prompt = document.getElementById("prompt")
const imagesSection = document.getElementById("generated")

imagesSection.hidden = true

btnelement.addEventListener("click", (ev) => {
    if (prompt.value.trim() == "") {
        alert("Enter Your Prompt First!!");
        prompt.focus();
    }
    else {
        btnelement.disabled=true
        btnelement.innerHTML=`<image src="./assets/img/spinner.svg" style="height:2rem">`
        promptInput=prompt.value
        fetch("/generate",{
            method:"POST",
            body:JSON.stringify({"prompt":promptInput}),
            mode:"same-origin",
            headers:{
                "Content-Type":"application/json"
            }
        }).then(res =>{
            if(res.status==403){
                res.json().then(val => {
                    btnelement.innerText="Generate"
                    btnelement.disabled=false
                    alert(val["msg"])
                })
            }else{
                imagesSection.hidden=true
                getResultInterval= setInterval(()=>{
                    fetch("/getGeneratedResults",{
                        mode:"same-origin",
                        method:"GET"
                    }).then(response=>{
                        if(response.status==200){
                            response.json().then((val)=>{
                                imagesSection.src=val['image_url']
                                imagesSection.hidden=false
                                btnelement.innerText="Generate"
                                btnelement.disabled=false
                                clearInterval(getResultInterval)
                            })
                        }else if(response.status==400){
                            response.json().then((val)=>{
                                btnelement.innerText="Generate"
                                btnelement.disabled=false
                                alert(val['msg'])
                                clearInterval(getResultInterval)
                            })
                        }
                    })
                },5000)
            }
        })
    }
})