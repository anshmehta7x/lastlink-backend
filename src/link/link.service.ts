import { supabase } from "../config/supabase";

export const getLinksByUsername = async (username: string) => {
    const { data, error } = await supabase
        .from("links")
        .select("*")
        .eq("owner", username);

    if (error) {
        throw new Error("Error getting links");
    }
    if (data.length === 0) {
        throw new Error("No links found");
    }

    return data;
};

export const createLink = async (linkData: {
    display_text: string;
    url: string;
    owner: string;
}) => {
    const { data, error } = await supabase
        .from("links")
        .insert(linkData)
        .select()
        .single();

    if (error) {
        throw new Error("Error creating link");
    }

    return data;
};

export const updateLink = async (
    linkId: string,
    updateData: { display_text?: string; url?: string },
) => {
    const { data, error } = await supabase
        .from("links")
        .update(updateData)
        .eq("linkid", linkId)
        .select()
        .single();

    if (error) {
        throw new Error("Error updating link");
    }
    if (!data) {
        throw new Error("Link not found");
    }

    return data;
};

export const deleteLink = async (linkId: string) => {
    const { data, error } = await supabase
        .from("links")
        .delete()
        .eq("linkid", linkId)
        .select()
        .single();

    if (error) {
        throw new Error("Error deleting link");
    }
    if (!data) {
        throw new Error("Link not found");
    }

    return data;
};
