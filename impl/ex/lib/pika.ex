defmodule Pika do
  alias Pika.Snowflake
  import Pika.Utils, only: [filter_prefixes: 2]

  @moduledoc false

  @spec valid_prefix?(binary()) :: boolean()
  defp valid_prefix?(prefix) do
    # Checks if `prefix` is alphanumeric
    Regex.match?(~r/^[0-9A-Za-z]+$/, prefix)
  end

  defp _gen(prefix, snowflake, secure) do
    unless secure do
      {:ok, "#{prefix}_#{Base.encode64(snowflake, padding: false)}"}
    end

    bytes = :rand.bytes(16)

    tail =
      "_s_#{Base.encode32(bytes, padding: false, case: :lower)}_#{snowflake}"

    {:ok, "#{prefix}_#{Base.encode64(tail, padding: false)}"}
  end

  @spec gen(binary()) :: {:error, binary()} | {:ok, binary()}
  def gen(prefix) do
    case valid_prefix?(prefix) do
      true ->
        prefixes = Application.get_env(:pika, :prefixes)

        case filter_prefixes(prefix, prefixes) do
          [prefix_record] ->
            snowflake = Snowflake.generate() |> Integer.to_string()

            _gen(prefix, snowflake, prefix_record[:secure])
          _ ->
            {:error, "Prefix is undefined"}
        end

      _ ->
        {:error, "Prefix is invalid (must be Alphanumeric)"}
    end
  end

  def gen!(prefix) do
    {:ok, id} = gen(prefix)

    id
  end

  def gen do
    {:error, "No prefix was specified"}
  end

  def deconstruct(id) do
    prefixes = Application.get_env(:pika, :prefixes)

    fragments = id |> String.split("_")
    [prefix, tail] = fragments

    [prefix_record] = Enum.filter(prefixes, fn m -> m.prefix == prefix end)
    decoded_tail = Base.decode64!(tail, padding: false)
    tail_fragments = decoded_tail |> String.split("_")
    snowflake = tail_fragments |> Enum.at(length(tail_fragments) - 1)

    decoded_snowflake = Snowflake.decode(snowflake)

    Map.merge(decoded_snowflake, %{
      prefix: prefix,
      tail: tail,
      snowflake: snowflake,
      prefix_record: prefix_record
    })
  end
end
