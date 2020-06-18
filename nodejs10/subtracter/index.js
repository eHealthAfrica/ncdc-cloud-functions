exports.subtracter = (req, res) => {
    const x = parseInt(req.query.x)
    const y = parseInt(req.query.y)
    return res.send(`${x - y}`);
};