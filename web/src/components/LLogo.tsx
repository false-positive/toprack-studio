function LLogo(props: React.ComponentProps<"svg">) {
    return (
        <svg fill="#000" width="800px" height="800px" viewBox="0 0 32 32" xmlns="http://www.w3.org/2000/svg" {...props}>
            <path d="M28 10h-5V6a2.002 2.002 0 00-2-2H11a2.002 2.002 0 00-2 2v4H4a2.002 2.002 0 00-2 2v16a2.002 2.002 0 002 2h24a2.002 2.002 0 002-2V12a2.002 2.002 0 00-2-2zM4 28V12h5v2H7v2h2v2H7v2h2v2H7v2h2v4zm17 0H11V6h10zm7 0h-5v-4h2v-2h-2v-2h2v-2h-2v-2h2v-2h-2v-2h5z" />
            <path d="M14 8H18V10H14z" />
            <path d="M14 12H18V14H14z" />
            <path d="M14 16H18V18H14z" />
            <path data-name="&lt;Transparent Rectangle&gt;" fill="none" d="M0 0H32V32H0z" />
        </svg>
    );
}

export default LLogo;
