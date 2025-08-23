import express_app from "./app";

const PORT = process.env.PORT || 1010;

express_app.listen(PORT, () => {
    console.log("Running server on port : ", PORT);
});
