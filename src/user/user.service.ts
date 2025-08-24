import { supabase } from "../config/supabase";

export const checkEmailAvailable = async (userEmail: string) => {
    const { data, error } = await supabase
        .from("users")
        .select("email")
        .eq("email", userEmail.trim().toLowerCase())
        .single();

    if (data !== null) {
        return false; // Email already taken
    }
    return true;
};

export const checkUserNameAvailable = async (userName: string) => {
    const { data, error } = await supabase
        .from("users")
        .select("username")
        .eq("username", userName.trim().toLowerCase())
        .single();

    if (data !== null) {
        return false; // Email already taken
    }
    return true;
};

interface reqUserInfo {
    email: string;
    username: string;
}

export const createUser = async (userData: reqUserInfo) => {
    if (!(await checkEmailAvailable(userData.email))) {
        throw new Error("Email taken");
    }
    if (!(await checkUserNameAvailable(userData.username))) {
        throw new Error("Username taken");
    }

    const { data, error } = await supabase
        .from("users")
        .insert({
            email: userData.email,
            username: userData.username,
        })
        .select("id, email, username")
        .single();
    if (error) {
        throw new Error("Error creating account");
    }

    return data;
};

export const getUserByUsername = async (userName: string) => {
    const { data, error } = await supabase
        .from("users")
        .select("id, email, username")
        .eq("username", userName.trim().toLowerCase())
        .single();
    if (data === null) {
        throw new Error("Username not found");
    }

    if (error) {
        throw new Error("Error fetching user");
    }

    return data;
};

export const removeUser = async (id: number) => {
    const { data, error } = await supabase
        .from("users")
        .delete()
        .eq("id", id)
        .select("id, email, username")
        .single();

    if (error) {
        throw new Error("Error removing user");
    }

    if (!data) {
        throw new Error("User not found");
    }

    return data;
};
