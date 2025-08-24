import express, { Application, Request, Response } from "express";
import dotenv from "dotenv";
import cors from "cors";

import userrouter from "./user/user.routes";
import linkrouter from "./link/link.routes";

const express_app: Application = express();
dotenv.config();

express_app.use(cors());
express_app.use(express.json());

const health_check = (request: Request, response: Response) => {
    console.log("Received ping from : ", request.ip);
    response.status(200).send({ status: "online" });
};

express_app.get("/api/health_check", health_check);
express_app.use("/api/user/", userrouter);
express_app.use("/api/link/", linkrouter);

export default express_app;
